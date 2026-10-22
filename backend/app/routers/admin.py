"""Administración de la estructura académica (facultades, programas, asignaturas, RA) y de los usuarios. Solo rol admin."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import (
    Asignatura,
    Facultad,
    Grupo,
    Pregunta,
    Programa,
    ResultadoAprendizaje,
    Usuario,
)
from app.schemas_academico import (
    AsignaturaEditarIn,
    AsignaturaIn,
    AsignaturaOut,
    AsignaturaRasIn,
    FacultadIn,
    FacultadOut,
    ProgramaEditarIn,
    ProgramaIn,
    ProgramaOut,
    RaEditarIn,
    RaIn,
    RaOut,
    UsuarioAdminIn,
    UsuarioAdminOut,
)
from app.seguridad import requiere_admin

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(requiere_admin)])


def _o404(obj, que: str):
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{que} no encontrado.")
    return obj


def _guardar(db: Session, mensaje_duplicado: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=mensaje_duplicado)


# ---------- Facultades ----------

def _facultad_out(db: Session, f: Facultad) -> FacultadOut:
    n = db.scalar(select(func.count()).select_from(Programa).where(Programa.facultad_id == f.id))
    return FacultadOut(id=f.id, nombre=f.nombre, num_programas=n or 0)


@router.get("/facultades", response_model=list[FacultadOut])
def listar_facultades(db: Session = Depends(get_db)):
    return [_facultad_out(db, f) for f in db.scalars(select(Facultad).order_by(Facultad.nombre))]


@router.post("/facultades", response_model=FacultadOut, status_code=201)
def crear_facultad(datos: FacultadIn, db: Session = Depends(get_db)):
    f = Facultad(nombre=datos.nombre.strip())
    db.add(f)
    _guardar(db, "Ya existe una facultad con ese nombre.")
    return _facultad_out(db, f)


@router.patch("/facultades/{facultad_id}", response_model=FacultadOut)
def editar_facultad(facultad_id: int, datos: FacultadIn, db: Session = Depends(get_db)):
    f = _o404(db.get(Facultad, facultad_id), "Facultad")
    f.nombre = datos.nombre.strip()
    _guardar(db, "Ya existe una facultad con ese nombre.")
    return _facultad_out(db, f)


@router.delete("/facultades/{facultad_id}", status_code=204)
def eliminar_facultad(facultad_id: int, db: Session = Depends(get_db)):
    f = _o404(db.get(Facultad, facultad_id), "Facultad")
    if _facultad_out(db, f).num_programas:
        raise HTTPException(status_code=409, detail="La facultad tiene programas. Elimínalos o muévelos primero.")
    db.delete(f)
    db.commit()


# ---------- Programas ----------

def _programa_out(p: Programa) -> ProgramaOut:
    return ProgramaOut(id=p.id, facultad_id=p.facultad_id, facultad=p.facultad.nombre, nombre=p.nombre, codigo=p.codigo)


@router.get("/programas", response_model=list[ProgramaOut])
def listar_programas(db: Session = Depends(get_db)):
    return [_programa_out(p) for p in db.scalars(select(Programa).order_by(Programa.nombre))]


@router.post("/programas", response_model=ProgramaOut, status_code=201)
def crear_programa(datos: ProgramaIn, db: Session = Depends(get_db)):
    _o404(db.get(Facultad, datos.facultad_id), "Facultad")
    p = Programa(facultad_id=datos.facultad_id, nombre=datos.nombre.strip(), codigo=datos.codigo.strip().upper())
    db.add(p)
    _guardar(db, "Ya existe un programa con ese código.")
    return _programa_out(p)


@router.patch("/programas/{programa_id}", response_model=ProgramaOut)
def editar_programa(programa_id: int, datos: ProgramaEditarIn, db: Session = Depends(get_db)):
    p = _o404(db.get(Programa, programa_id), "Programa")
    if datos.facultad_id is not None:
        _o404(db.get(Facultad, datos.facultad_id), "Facultad")
        p.facultad_id = datos.facultad_id
    if datos.nombre is not None:
        p.nombre = datos.nombre.strip()
    if datos.codigo is not None:
        p.codigo = datos.codigo.strip().upper()
    _guardar(db, "Ya existe un programa con ese código.")
    db.refresh(p)
    return _programa_out(p)


@router.delete("/programas/{programa_id}", status_code=204)
def eliminar_programa(programa_id: int, db: Session = Depends(get_db)):
    p = _o404(db.get(Programa, programa_id), "Programa")
    if p.asignaturas or p.resultados:
        raise HTTPException(status_code=409, detail="El programa tiene asignaturas o resultados de aprendizaje. Elimínalos primero.")
    db.execute(update(Usuario).where(Usuario.programa_id == p.id).values(programa_id=None))
    db.delete(p)
    db.commit()


# ---------- Asignaturas ----------

def _asignatura_out(a: Asignatura) -> AsignaturaOut:
    return AsignaturaOut(
        id=a.id, programa_id=a.programa_id, programa=a.programa.nombre, nombre=a.nombre,
        codigo=a.codigo, semestre=a.semestre, ra_ids=sorted(r.id for r in a.resultados),
    )


@router.get("/asignaturas", response_model=list[AsignaturaOut])
def listar_asignaturas(programa_id: int | None = None, db: Session = Depends(get_db)):
    consulta = select(Asignatura).order_by(Asignatura.semestre, Asignatura.nombre)
    if programa_id is not None:
        consulta = consulta.where(Asignatura.programa_id == programa_id)
    return [_asignatura_out(a) for a in db.scalars(consulta)]


@router.post("/asignaturas", response_model=AsignaturaOut, status_code=201)
def crear_asignatura(datos: AsignaturaIn, db: Session = Depends(get_db)):
    _o404(db.get(Programa, datos.programa_id), "Programa")
    a = Asignatura(programa_id=datos.programa_id, nombre=datos.nombre.strip(), codigo=datos.codigo.strip().upper(), semestre=datos.semestre)
    db.add(a)
    db.commit()
    return _asignatura_out(a)


@router.patch("/asignaturas/{asignatura_id}", response_model=AsignaturaOut)
def editar_asignatura(asignatura_id: int, datos: AsignaturaEditarIn, db: Session = Depends(get_db)):
    a = _o404(db.get(Asignatura, asignatura_id), "Asignatura")
    if datos.nombre is not None:
        a.nombre = datos.nombre.strip()
    if datos.codigo is not None:
        a.codigo = datos.codigo.strip().upper()
    if datos.semestre is not None:
        a.semestre = datos.semestre
    db.commit()
    return _asignatura_out(a)


@router.put("/asignaturas/{asignatura_id}/ras", response_model=AsignaturaOut)
def asignar_ras(asignatura_id: int, datos: AsignaturaRasIn, db: Session = Depends(get_db)):
    """Define qué resultados de aprendizaje aporta la asignatura (deben ser de su mismo programa)."""
    a = _o404(db.get(Asignatura, asignatura_id), "Asignatura")
    ras = list(db.scalars(select(ResultadoAprendizaje).where(ResultadoAprendizaje.id.in_(set(datos.ra_ids)))))
    if len(ras) != len(set(datos.ra_ids)):
        raise HTTPException(status_code=404, detail="Algún resultado de aprendizaje no existe.")
    if any(r.programa_id != a.programa_id for r in ras):
        raise HTTPException(status_code=400, detail="Los resultados de aprendizaje deben ser del mismo programa que la asignatura.")
    a.resultados = ras
    db.commit()
    return _asignatura_out(a)


@router.delete("/asignaturas/{asignatura_id}", status_code=204)
def eliminar_asignatura(asignatura_id: int, db: Session = Depends(get_db)):
    a = _o404(db.get(Asignatura, asignatura_id), "Asignatura")
    if a.grupos:
        raise HTTPException(status_code=409, detail="La asignatura tiene grupos creados. No se puede eliminar.")
    a.resultados = []
    db.delete(a)
    db.commit()


# ---------- Resultados de aprendizaje ----------

def _ra_out(r: ResultadoAprendizaje) -> RaOut:
    return RaOut(id=r.id, programa_id=r.programa_id, programa=r.programa.nombre, codigo=r.codigo, descripcion=r.descripcion)


@router.get("/ras", response_model=list[RaOut])
def listar_ras(programa_id: int | None = None, db: Session = Depends(get_db)):
    consulta = select(ResultadoAprendizaje).order_by(ResultadoAprendizaje.programa_id, ResultadoAprendizaje.codigo)
    if programa_id is not None:
        consulta = consulta.where(ResultadoAprendizaje.programa_id == programa_id)
    return [_ra_out(r) for r in db.scalars(consulta)]


@router.post("/ras", response_model=RaOut, status_code=201)
def crear_ra(datos: RaIn, db: Session = Depends(get_db)):
    _o404(db.get(Programa, datos.programa_id), "Programa")
    r = ResultadoAprendizaje(programa_id=datos.programa_id, codigo=datos.codigo.strip().upper(), descripcion=datos.descripcion.strip())
    db.add(r)
    _guardar(db, "Ese programa ya tiene un resultado de aprendizaje con ese código.")
    return _ra_out(r)


@router.patch("/ras/{ra_id}", response_model=RaOut)
def editar_ra(ra_id: int, datos: RaEditarIn, db: Session = Depends(get_db)):
    r = _o404(db.get(ResultadoAprendizaje, ra_id), "Resultado de aprendizaje")
    if datos.codigo is not None:
        r.codigo = datos.codigo.strip().upper()
    if datos.descripcion is not None:
        r.descripcion = datos.descripcion.strip()
    _guardar(db, "Ese programa ya tiene un resultado de aprendizaje con ese código.")
    return _ra_out(r)


@router.delete("/ras/{ra_id}", status_code=204)
def eliminar_ra(ra_id: int, db: Session = Depends(get_db)):
    r = _o404(db.get(ResultadoAprendizaje, ra_id), "Resultado de aprendizaje")
    db.execute(update(Pregunta).where(Pregunta.ra_id == r.id).values(ra_id=None))
    for a in db.scalars(select(Asignatura).where(Asignatura.programa_id == r.programa_id)):
        if r in a.resultados:
            a.resultados.remove(r)
    db.delete(r)
    db.commit()


# ---------- Usuarios ----------

def _usuario_out(u: Usuario, db: Session) -> UsuarioAdminOut:
    programa = db.get(Programa, u.programa_id) if u.programa_id else None
    return UsuarioAdminOut(id=u.id, nombre=u.nombre, email=u.email, rol=u.rol, programa_id=u.programa_id,
                           programa=programa.nombre if programa else None)


@router.get("/usuarios", response_model=list[UsuarioAdminOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return [_usuario_out(u, db) for u in db.scalars(select(Usuario).order_by(Usuario.nombre))]


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioAdminOut)
def editar_usuario(
    usuario_id: int,
    datos: UsuarioAdminIn,
    admin: Usuario = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    u = _o404(db.get(Usuario, usuario_id), "Usuario")
    if datos.rol is not None:
        if u.id == admin.id and datos.rol != "admin":
            raise HTTPException(status_code=400, detail="No puedes quitarte a ti mismo el rol de administrador.")
        u.rol = datos.rol
    if "programa_id" in datos.model_fields_set:
        if datos.programa_id is not None:
            _o404(db.get(Programa, datos.programa_id), "Programa")
        u.programa_id = datos.programa_id
    if u.rol != "coordinador":
        u.programa_id = None  # el programa solo tiene sentido para el coordinador
    db.commit()
    return _usuario_out(u, db)
