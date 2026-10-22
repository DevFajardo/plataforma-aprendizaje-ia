"""Banco de preguntas institucional: guardar preguntas de un cuestionario, buscarlas y reutilizarlas."""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Cuestionario, Intento, Pregunta, PreguntaBanco, ResultadoAprendizaje, Usuario
from app.routers.docente import _propio, _pregunta_propia
from app.schemas_api import VerificacionOut
from app.schemas_s8 import (
    AgregarDesdeBancoIn,
    EditarBancoIn,
    EstadisticaBanco,
    FiltrosBanco,
    GuardarEnBancoIn,
    PaginaBanco,
    PreguntaBancoOut,
)
from app.seguridad import requiere_docente, requiere_seguimiento

router = APIRouter(prefix="/api", tags=["banco"])


def _limpiar_etiquetas(etiquetas: list[str]) -> list[str]:
    vistas: list[str] = []
    for e in etiquetas:
        e = " ".join(e.split())[:30]
        if e and e.lower() not in {v.lower() for v in vistas}:
            vistas.append(e)
    return vistas[:10]


def _estado_verificacion(texto: str | None) -> str:
    if not texto:
        return "sin_verificar"
    try:
        return VerificacionOut.model_validate_json(texto).estado
    except ValueError:
        return "sin_verificar"


def _estadisticas(db: Session, ids: list[int]) -> dict[int, EstadisticaBanco]:
    """Respuestas y % de acierto acumulados de las copias de cada pregunta del banco (intentos finalizados)."""
    if not ids:
        return {}
    copias = db.execute(
        select(Pregunta.id, Pregunta.banco_id, Pregunta.cuestionario_id, Pregunta.tipo).where(Pregunta.banco_id.in_(ids))
    ).all()
    por_cuestionario: dict[int, list[tuple[int, int, str]]] = {}
    usos: dict[int, set[int]] = {}
    for pid, bid, cid, tipo in copias:
        por_cuestionario.setdefault(cid, []).append((pid, bid, tipo))
        usos.setdefault(bid, set()).add(cid)
    respuestas = {i: 0 for i in ids}
    aciertos = {i: 0 for i in ids}
    if por_cuestionario:
        for intento in db.scalars(
            select(Intento).where(Intento.cuestionario_id.in_(list(por_cuestionario)), Intento.finalizado.is_(True))
        ):
            mapa = {pid: (bid, tipo) for pid, bid, tipo in por_cuestionario[intento.cuestionario_id]}
            for r in json.loads(intento.respuestas_json):
                dato = mapa.get(r["pregunta_id"])
                if dato is None or dato[1] == "abierta":
                    continue
                respuestas[dato[0]] += 1
                aciertos[dato[0]] += 1 if r.get("correcta") is True else 0
    return {
        i: EstadisticaBanco(
            respuestas=respuestas[i],
            porcentaje_acierto=round(100 * aciertos[i] / respuestas[i], 1) if respuestas[i] else None,
            usos=len(usos.get(i, ())),
        )
        for i in ids
        if i in usos
    }


def _salida(b: PreguntaBanco, usuario: Usuario, estadisticas: dict[int, EstadisticaBanco]) -> PreguntaBancoOut:
    verificacion = None
    if b.verificacion:
        try:
            verificacion = VerificacionOut.model_validate_json(b.verificacion)
        except ValueError:
            verificacion = None
    return PreguntaBancoOut(
        id=b.id,
        autor=b.autor.nombre,
        es_mia=b.autor_id == usuario.id,
        visibilidad=b.visibilidad,
        tipo=b.tipo,
        enunciado=b.enunciado,
        opciones=json.loads(b.opciones_json),
        respuesta_correcta=b.respuesta_correcta,
        explicacion=b.explicacion,
        nivel_bloom=b.nivel_bloom,
        ra_codigo=b.ra_codigo,
        ra_descripcion=b.ra_descripcion,
        asignatura_nombre=b.asignatura_nombre,
        etiquetas=json.loads(b.etiquetas_json),
        verificacion=verificacion,
        estado_verificacion=verificacion.estado if verificacion else "sin_verificar",
        estadisticas=estadisticas.get(b.id),
        creado_en=b.creado_en,
    )


def _visibles(usuario: Usuario):
    """Condición SQL: institucionales de cualquiera y privadas solo del autor."""
    return or_(PreguntaBanco.visibilidad == "institucional", PreguntaBanco.autor_id == usuario.id)


def _banco_visible(db: Session, banco_id: int, usuario: Usuario) -> PreguntaBanco:
    b = db.get(PreguntaBanco, banco_id)
    # Una privada ajena se trata como inexistente (no revela que existe)
    if b is None or (b.visibilidad == "privada" and b.autor_id != usuario.id):
        raise HTTPException(status_code=404, detail="Pregunta del banco no encontrada.")
    return b


@router.post("/preguntas/{pregunta_id}/banco", response_model=PreguntaBancoOut, status_code=201)
def guardar_en_banco(
    pregunta_id: int,
    datos: GuardarEnBancoIn,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    """Copia la pregunta al banco con su RA, nivel de Bloom, asignatura, etiquetas y autor."""
    p = _pregunta_propia(db, pregunta_id, docente)
    if p.banco_id and db.get(PreguntaBanco, p.banco_id) is not None:
        raise HTTPException(status_code=409, detail="Esta pregunta ya está en el banco.")
    c = p.cuestionario
    asignatura = c.grupo.asignatura.nombre if c.grupo_id and c.grupo else (datos.asignatura_nombre or "").strip() or None
    ra = db.get(ResultadoAprendizaje, p.ra_id) if p.ra_id else None
    b = PreguntaBanco(
        autor_id=docente.id,
        visibilidad=datos.visibilidad,
        tipo=p.tipo,
        enunciado=p.enunciado,
        opciones_json=p.opciones_json,
        respuesta_correcta=p.respuesta_correcta,
        explicacion=p.explicacion,
        nivel_bloom=p.nivel_bloom,
        ra_codigo=ra.codigo if ra else None,
        ra_descripcion=ra.descripcion if ra else None,
        asignatura_nombre=asignatura,
        etiquetas_json=json.dumps(_limpiar_etiquetas(datos.etiquetas), ensure_ascii=False),
        verificacion=p.verificacion,
    )
    db.add(b)
    db.flush()
    p.banco_id = b.id
    db.commit()
    return _salida(b, docente, {})


@router.get("/banco", response_model=PaginaBanco)
def buscar_banco(
    q: str = Query(default="", max_length=200),
    asignatura: str = Query(default="", max_length=150),
    ra: str = Query(default="", max_length=20),
    bloom: str = Query(default="", max_length=15),
    tipo: str = Query(default="", max_length=30),
    verificacion: str = Query(default="", pattern="^(|verificada|revisar|sin_verificar)$"),
    solo_mias: bool = False,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=50),
    usuario: Usuario = Depends(requiere_seguimiento),
    db: Session = Depends(get_db),
):
    cond = [PreguntaBanco.autor_id == usuario.id] if solo_mias else [_visibles(usuario)]
    for palabra in q.lower().split():
        patron = f"%{palabra}%"
        cond.append(
            or_(
                func.lower(PreguntaBanco.enunciado).like(patron),
                func.lower(PreguntaBanco.opciones_json).like(patron),
                func.lower(PreguntaBanco.etiquetas_json).like(patron),
                func.lower(PreguntaBanco.respuesta_correcta).like(patron),
            )
        )
    if asignatura:
        cond.append(PreguntaBanco.asignatura_nombre == asignatura)
    if ra:
        cond.append(PreguntaBanco.ra_codigo == ra)
    if bloom:
        cond.append(PreguntaBanco.nivel_bloom == bloom)
    if tipo:
        cond.append(PreguntaBanco.tipo == tipo)
    if verificacion == "sin_verificar":
        cond.append(PreguntaBanco.verificacion.is_(None))
    elif verificacion:
        cond.append(PreguntaBanco.verificacion.like(f'%"estado": "{verificacion}"%'))
    donde = and_(*cond)
    total = db.scalar(select(func.count()).select_from(PreguntaBanco).where(donde)) or 0
    filas = db.scalars(
        select(PreguntaBanco).where(donde).order_by(PreguntaBanco.id.desc()).offset((pagina - 1) * por_pagina).limit(por_pagina)
    ).all()
    stats = _estadisticas(db, [b.id for b in filas])
    return PaginaBanco(total=total, pagina=pagina, por_pagina=por_pagina, items=[_salida(b, usuario, stats) for b in filas])


@router.get("/banco/filtros", response_model=FiltrosBanco)
def filtros_banco(usuario: Usuario = Depends(requiere_seguimiento), db: Session = Depends(get_db)):
    def valores(col):
        return sorted(v for v in db.scalars(select(col).where(_visibles(usuario), col.is_not(None)).distinct()) if v)

    return FiltrosBanco(asignaturas=valores(PreguntaBanco.asignatura_nombre), ras=valores(PreguntaBanco.ra_codigo))


@router.patch("/banco/{banco_id}", response_model=PreguntaBancoOut)
def editar_banco(
    banco_id: int,
    datos: EditarBancoIn,
    usuario: Usuario = Depends(requiere_seguimiento),
    db: Session = Depends(get_db),
):
    b = _banco_visible(db, banco_id, usuario)
    if b.autor_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo el autor puede modificar esta pregunta del banco.")
    if datos.visibilidad is not None:
        b.visibilidad = datos.visibilidad
    if datos.etiquetas is not None:
        b.etiquetas_json = json.dumps(_limpiar_etiquetas(datos.etiquetas), ensure_ascii=False)
    db.commit()
    return _salida(b, usuario, _estadisticas(db, [b.id]))


@router.delete("/banco/{banco_id}", status_code=204)
def eliminar_banco(banco_id: int, usuario: Usuario = Depends(requiere_seguimiento), db: Session = Depends(get_db)):
    b = _banco_visible(db, banco_id, usuario)
    if b.autor_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo el autor puede eliminar esta pregunta del banco.")
    for p in db.scalars(select(Pregunta).where(Pregunta.banco_id == b.id)):
        p.banco_id = None
    db.delete(b)
    db.commit()


@router.post("/banco/{banco_id}/agregar", status_code=201)
def agregar_a_cuestionario(
    banco_id: int,
    datos: AgregarDesdeBancoIn,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    """Copia la pregunta del banco al final de un cuestionario propio."""
    b = _banco_visible(db, banco_id, docente)
    c: Cuestionario = _propio(db, datos.cuestionario_id, docente)
    ra_id = None
    if b.ra_codigo and c.grupo_id and c.grupo:  # se asigna el RA si la asignatura del grupo tiene uno con el mismo código
        ra_id = next((r.id for r in c.grupo.asignatura.resultados if r.codigo == b.ra_codigo), None)
    p = Pregunta(
        cuestionario_id=c.id,
        orden=max((x.orden for x in c.preguntas), default=-1) + 1,
        tipo=b.tipo,
        enunciado=b.enunciado,
        opciones_json=b.opciones_json,
        respuesta_correcta=b.respuesta_correcta,
        explicacion=b.explicacion,
        marca_tiempo="",  # la marca de tiempo pertenece al video de origen
        ra_id=ra_id,
        nivel_bloom=b.nivel_bloom,
        verificacion=None,  # la verificación pertenece al video de origen; aquí queda sin verificar
        banco_id=b.id,
    )
    db.add(p)
    db.flush()
    c.num_preguntas = len(c.preguntas) + 1
    db.commit()
    return {"pregunta_id": p.id, "cuestionario_id": c.id, "num_preguntas": c.num_preguntas}
