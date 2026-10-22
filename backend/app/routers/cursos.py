"""Cursos: grupos del docente, matrícula de estudiantes con código de ingreso y vista «Mis cursos»."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import (
    AlertaSeguimiento,
    Asignatura,
    Cuestionario,
    Grupo,
    Intento,
    Matricula,
    Usuario,
    generar_codigo,
)
from app.schemas_academico import (
    AsignaturaOut,
    CuestionarioCursoOut,
    GrupoEditarIn,
    GrupoIn,
    GrupoOut,
    MatriculadoOut,
    MiCursoOut,
    UnirseGrupoIn,
)
from app.seguridad import requiere_rol, requiere_seguimiento

router = APIRouter(prefix="/api", tags=["cursos"])

requiere_docente_o_admin = requiere_rol("docente", "admin")


def grupos_visibles(db: Session, usuario: Usuario) -> list[Grupo]:
    """Grupos que el usuario puede consultar: los suyos (docente), los de su programa (coordinador) o todos (admin)."""
    consulta = select(Grupo).order_by(Grupo.periodo.desc(), Grupo.nombre)
    if usuario.rol == "docente":
        consulta = consulta.where(Grupo.docente_id == usuario.id)
    elif usuario.rol == "coordinador":
        if usuario.programa_id is None:
            return []
        consulta = consulta.join(Asignatura, Asignatura.id == Grupo.asignatura_id).where(
            Asignatura.programa_id == usuario.programa_id
        )
    elif usuario.rol != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción.")
    return list(db.scalars(consulta))


def _grupo_out(db: Session, g: Grupo) -> GrupoOut:
    return GrupoOut(
        id=g.id,
        nombre=g.nombre,
        periodo=g.periodo,
        codigo_ingreso=g.codigo_ingreso,
        asignatura_id=g.asignatura_id,
        asignatura=g.asignatura.nombre,
        programa=g.asignatura.programa.nombre,
        docente=g.docente.nombre,
        num_matriculados=db.scalar(select(func.count()).select_from(Matricula).where(Matricula.grupo_id == g.id)) or 0,
        num_cuestionarios=db.scalar(select(func.count()).select_from(Cuestionario).where(Cuestionario.grupo_id == g.id)) or 0,
    )


def _grupo_gestionable(db: Session, grupo_id: int, usuario: Usuario) -> Grupo:
    """Grupo del docente (el admin puede gestionar cualquiera)."""
    g = db.get(Grupo, grupo_id)
    if g is None:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    if usuario.rol != "admin" and g.docente_id != usuario.id:
        raise HTTPException(status_code=403, detail="Ese grupo pertenece a otro docente.")
    return g


def _codigo_libre(db: Session) -> str:
    while True:
        codigo = generar_codigo()
        if not db.scalar(select(Grupo.id).where(Grupo.codigo_ingreso == codigo)):
            return codigo


# ---------- Catálogo para crear grupos ----------

@router.get("/catalogo/asignaturas", response_model=list[AsignaturaOut])
def catalogo_asignaturas(_: Usuario = Depends(requiere_seguimiento), db: Session = Depends(get_db)):
    return [
        AsignaturaOut(
            id=a.id, programa_id=a.programa_id, programa=a.programa.nombre, nombre=a.nombre, codigo=a.codigo,
            semestre=a.semestre, ra_ids=sorted(r.id for r in a.resultados),
        )
        for a in db.scalars(select(Asignatura).order_by(Asignatura.programa_id, Asignatura.semestre, Asignatura.nombre))
    ]


# ---------- Grupos (docente) ----------

@router.get("/grupos", response_model=list[GrupoOut])
def listar_grupos(usuario: Usuario = Depends(requiere_seguimiento), db: Session = Depends(get_db)):
    return [_grupo_out(db, g) for g in grupos_visibles(db, usuario)]


@router.post("/grupos", response_model=GrupoOut, status_code=201)
def crear_grupo(datos: GrupoIn, docente: Usuario = Depends(requiere_rol("docente")), db: Session = Depends(get_db)):
    if db.get(Asignatura, datos.asignatura_id) is None:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada.")
    g = Grupo(
        asignatura_id=datos.asignatura_id,
        docente_id=docente.id,
        periodo=datos.periodo,
        nombre=datos.nombre.strip(),
        codigo_ingreso=_codigo_libre(db),
    )
    db.add(g)
    db.commit()
    return _grupo_out(db, g)


@router.patch("/grupos/{grupo_id}", response_model=GrupoOut)
def editar_grupo(grupo_id: int, datos: GrupoEditarIn, usuario: Usuario = Depends(requiere_docente_o_admin), db: Session = Depends(get_db)):
    g = _grupo_gestionable(db, grupo_id, usuario)
    if datos.nombre is not None:
        g.nombre = datos.nombre.strip()
    if datos.periodo is not None:
        g.periodo = datos.periodo
    db.commit()
    return _grupo_out(db, g)


@router.post("/grupos/{grupo_id}/nuevo-codigo", response_model=GrupoOut)
def renovar_codigo(grupo_id: int, usuario: Usuario = Depends(requiere_docente_o_admin), db: Session = Depends(get_db)):
    """Cambia el código de ingreso (p. ej. si se filtró). Los ya matriculados siguen en el grupo."""
    g = _grupo_gestionable(db, grupo_id, usuario)
    g.codigo_ingreso = _codigo_libre(db)
    db.commit()
    return _grupo_out(db, g)


@router.delete("/grupos/{grupo_id}", status_code=204)
def eliminar_grupo(grupo_id: int, usuario: Usuario = Depends(requiere_docente_o_admin), db: Session = Depends(get_db)):
    g = _grupo_gestionable(db, grupo_id, usuario)
    db.execute(update(Cuestionario).where(Cuestionario.grupo_id == g.id).values(grupo_id=None))
    db.execute(delete(AlertaSeguimiento).where(AlertaSeguimiento.grupo_id == g.id))
    db.delete(g)
    db.commit()


@router.get("/grupos/{grupo_id}/matriculados", response_model=list[MatriculadoOut])
def matriculados(grupo_id: int, usuario: Usuario = Depends(requiere_seguimiento), db: Session = Depends(get_db)):
    g = db.get(Grupo, grupo_id)
    if g is None or g not in grupos_visibles(db, usuario):
        raise HTTPException(status_code=404 if g is None else 403, detail="Grupo no encontrado." if g is None else "No tienes acceso a ese grupo.")
    filas = db.execute(
        select(Matricula, Usuario).join(Usuario, Usuario.id == Matricula.estudiante_id)
        .where(Matricula.grupo_id == g.id).order_by(Usuario.nombre)
    ).all()
    return [MatriculadoOut(estudiante_id=u.id, nombre=u.nombre, email=u.email, desde=m.creado_en) for m, u in filas]


@router.delete("/grupos/{grupo_id}/matriculados/{estudiante_id}", status_code=204)
def quitar_matriculado(grupo_id: int, estudiante_id: int, usuario: Usuario = Depends(requiere_docente_o_admin), db: Session = Depends(get_db)):
    g = _grupo_gestionable(db, grupo_id, usuario)
    m = db.scalar(select(Matricula).where(Matricula.grupo_id == g.id, Matricula.estudiante_id == estudiante_id))
    if m is None:
        raise HTTPException(status_code=404, detail="Ese estudiante no está matriculado en el grupo.")
    db.delete(m)
    db.commit()


# ---------- Mis cursos (estudiante) ----------

@router.post("/mis-cursos/unirse", response_model=MiCursoOut)
def unirse(datos: UnirseGrupoIn, estudiante: Usuario = Depends(requiere_rol("estudiante")), db: Session = Depends(get_db)):
    g = db.scalar(select(Grupo).where(Grupo.codigo_ingreso == datos.codigo.strip().upper()))
    if g is None:
        raise HTTPException(status_code=404, detail="No existe ningún curso con ese código. Revisa que esté bien escrito.")
    if db.scalar(select(Matricula.id).where(Matricula.grupo_id == g.id, Matricula.estudiante_id == estudiante.id)):
        raise HTTPException(status_code=409, detail="Ya estás matriculado en este curso.")
    db.add(Matricula(grupo_id=g.id, estudiante_id=estudiante.id))
    db.commit()
    return _mi_curso(db, g, estudiante)


def _mi_curso(db: Session, g: Grupo, estudiante: Usuario) -> MiCursoOut:
    cuestionarios = db.scalars(
        select(Cuestionario)
        .where(Cuestionario.grupo_id == g.id, Cuestionario.publicado.is_(True))
        .order_by(Cuestionario.publicado_en.desc(), Cuestionario.id.desc())
    ).all()
    mejores: dict[int, Intento] = {}
    if cuestionarios:
        intentos = db.scalars(
            select(Intento).where(
                Intento.usuario_id == estudiante.id,
                Intento.finalizado.is_(True),
                Intento.cuestionario_id.in_([c.id for c in cuestionarios]),
            )
        )
        for i in intentos:
            if i.cuestionario_id not in mejores or i.puntaje > mejores[i.cuestionario_id].puntaje:
                mejores[i.cuestionario_id] = i
    return MiCursoOut(
        grupo_id=g.id,
        nombre=g.nombre,
        periodo=g.periodo,
        asignatura=g.asignatura.nombre,
        programa=g.asignatura.programa.nombre,
        docente=g.docente.nombre,
        cuestionarios=[
            CuestionarioCursoOut(
                id=c.id,
                titulo=c.titulo,
                num_preguntas=c.num_preguntas,
                mejor_puntaje=mejores[c.id].puntaje if c.id in mejores else None,
                mejor_total=mejores[c.id].total if c.id in mejores else None,
            )
            for c in cuestionarios
        ],
    )


@router.get("/mis-cursos", response_model=list[MiCursoOut])
def mis_cursos(estudiante: Usuario = Depends(requiere_rol("estudiante")), db: Session = Depends(get_db)):
    grupos = db.scalars(
        select(Grupo).join(Matricula, Matricula.grupo_id == Grupo.id)
        .where(Matricula.estudiante_id == estudiante.id).order_by(Grupo.periodo.desc(), Grupo.nombre)
    ).all()
    return [_mi_curso(db, g, estudiante) for g in grupos]


@router.delete("/mis-cursos/{grupo_id}", status_code=204)
def salir_del_curso(grupo_id: int, estudiante: Usuario = Depends(requiere_rol("estudiante")), db: Session = Depends(get_db)):
    m = db.scalar(select(Matricula).where(Matricula.grupo_id == grupo_id, Matricula.estudiante_id == estudiante.id))
    if m is None:
        raise HTTPException(status_code=404, detail="No estás matriculado en ese curso.")
    db.delete(m)
    db.commit()
