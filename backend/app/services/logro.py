"""Logro por resultado de aprendizaje (RA), nivel de Bloom, asignatura/grupo y tendencia semanal.

Reglas (explicables):
- Solo cuentan las respuestas a preguntas cerradas (las abiertas no se califican) de intentos FINALIZADOS de
  estudiantes MATRICULADOS en el grupo al que está asignado el cuestionario (el creador no cuenta).
- Logro = aciertos / respuestas x 100. Semáforo: >= 70 verde, 50 a 69 amarillo, < 50 rojo.
"""
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos import (
    NIVELES_BLOOM,
    Asignatura,
    Cuestionario,
    Grupo,
    Intento,
    Matricula,
    Pregunta,
    Programa,
    ResultadoAprendizaje,
    Usuario,
    como_utc,
)
from app.schemas_academico import (
    CoordinacionOut,
    LogroAsignatura,
    LogroBloom,
    LogroGrupo,
    LogroRa,
    ProgramaBasico,
    PuntoTendencia,
)

UMBRAL_VERDE = 70
UMBRAL_AMARILLO = 50


def semaforo(logro: float | None) -> str:
    if logro is None:
        return "sin_datos"
    if logro >= UMBRAL_VERDE:
        return "verde"
    return "amarillo" if logro >= UMBRAL_AMARILLO else "rojo"


@dataclass
class Resp:
    """Una respuesta calificada (acierto o error) a una pregunta cerrada."""

    asignatura_id: int
    grupo_id: int
    ra_id: int | None
    bloom: str | None
    pregunta_id: int
    correcta: bool
    usuario_id: int
    fecha: datetime


def programas_del_usuario(db: Session, usuario: Usuario) -> list[Programa]:
    """Programas que el usuario puede consultar: el suyo (coordinador) o todos (admin)."""
    if usuario.rol == "admin":
        return list(db.scalars(select(Programa).order_by(Programa.nombre)))
    if usuario.rol == "coordinador":
        if usuario.programa_id is None:
            raise HTTPException(status_code=400, detail="Tu cuenta de coordinador aún no tiene un programa asignado. Pídeselo al administrador.")
        p = db.get(Programa, usuario.programa_id)
        return [p] if p else []
    raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción.")


def alcance(db: Session, usuario: Usuario, programa_id: int | None) -> tuple[list[Programa], list[Programa]]:
    """(programas disponibles, programas consultados). El coordinador solo ve el suyo; el admin elige uno o ve todos."""
    disponibles = programas_del_usuario(db, usuario)
    if programa_id is None:
        return disponibles, disponibles
    elegido = [p for p in disponibles if p.id == programa_id]
    if not elegido:
        raise HTTPException(status_code=403, detail="No tienes acceso a ese programa.")
    return disponibles, elegido


def _lunes(fecha: datetime) -> str:
    d: date = como_utc(fecha).date()
    return (d - timedelta(days=d.weekday())).isoformat()


def recolectar(db: Session, programa_ids: list[int], periodo: str | None = None) -> tuple[list[Resp], dict[int, Pregunta]]:
    """Respuestas calificadas de los programas indicados (opcionalmente filtradas por periodo)."""
    consulta = (
        select(Cuestionario, Grupo, Asignatura)
        .join(Grupo, Grupo.id == Cuestionario.grupo_id)
        .join(Asignatura, Asignatura.id == Grupo.asignatura_id)
        .where(Asignatura.programa_id.in_(programa_ids))
    )
    if periodo:
        consulta = consulta.where(Grupo.periodo == periodo)
    filas = db.execute(consulta).all()
    if not filas:
        return [], {}
    cuestionarios = {c.id: (c, g, a) for c, g, a in filas}
    preguntas = {
        p.id: p
        for p in db.scalars(select(Pregunta).where(Pregunta.cuestionario_id.in_(cuestionarios), Pregunta.tipo != "abierta"))
    }
    matriculados = {
        (m.grupo_id, m.estudiante_id)
        for m in db.scalars(select(Matricula).where(Matricula.grupo_id.in_({g.id for _, g, _ in filas})))
    }
    resps: list[Resp] = []
    for intento in db.scalars(
        select(Intento).where(Intento.cuestionario_id.in_(cuestionarios), Intento.finalizado.is_(True))
    ):
        c, g, a = cuestionarios[intento.cuestionario_id]
        if intento.usuario_id == c.creador_id or (g.id, intento.usuario_id) not in matriculados:
            continue
        for r in json.loads(intento.respuestas_json):
            p = preguntas.get(r.get("pregunta_id"))
            if p is None or r.get("correcta") not in (True, False):
                continue
            resps.append(Resp(a.id, g.id, p.ra_id, p.nivel_bloom, p.id, r["correcta"] is True, intento.usuario_id, intento.creado_en))
    return resps, preguntas


def _logro(rs: list[Resp]) -> float | None:
    return round(100 * sum(1 for r in rs if r.correcta) / len(rs), 1) if rs else None


def periodos_disponibles(db: Session, programa_ids: list[int]) -> list[str]:
    return sorted(
        set(
            db.scalars(
                select(Grupo.periodo).join(Asignatura, Asignatura.id == Grupo.asignatura_id)
                .where(Asignatura.programa_id.in_(programa_ids))
            )
        ),
        reverse=True,
    )


def calcular_coordinacion(db: Session, usuario: Usuario, programa_id: int | None, periodo: str | None) -> CoordinacionOut:
    disponibles, consultados = alcance(db, usuario, programa_id)
    ids = [p.id for p in consultados]
    resps, preguntas = recolectar(db, ids, periodo or None)

    # --- Por resultado de aprendizaje ---
    por_ra: dict[int, list[Resp]] = defaultdict(list)
    por_bloom: dict[str, list[Resp]] = defaultdict(list)
    for r in resps:
        if r.ra_id is not None:
            por_ra[r.ra_id].append(r)
        if r.bloom:
            por_bloom[r.bloom].append(r)
    ras = []
    for ra in db.scalars(
        select(ResultadoAprendizaje).where(ResultadoAprendizaje.programa_id.in_(ids))
        .order_by(ResultadoAprendizaje.programa_id, ResultadoAprendizaje.codigo)
    ):
        rs = por_ra.get(ra.id, [])
        logro = _logro(rs)
        ras.append(LogroRa(
            ra_id=ra.id, codigo=ra.codigo, descripcion=ra.descripcion, programa=ra.programa.nombre, logro=logro,
            respuestas=len(rs), estudiantes=len({r.usuario_id for r in rs}), semaforo=semaforo(logro),
        ))

    # --- Distribución por nivel de Bloom ---
    preguntas_bloom: dict[str, set[int]] = defaultdict(set)
    for p in preguntas.values():
        if p.nivel_bloom:
            preguntas_bloom[p.nivel_bloom].add(p.id)
    bloom = [
        LogroBloom(nivel=n, preguntas=len(preguntas_bloom.get(n, ())), respuestas=len(por_bloom.get(n, [])), logro=_logro(por_bloom.get(n, [])))
        for n in NIVELES_BLOOM
    ]

    # --- Por asignatura y grupo ---
    por_asig: dict[int, list[Resp]] = defaultdict(list)
    por_grupo: dict[int, list[Resp]] = defaultdict(list)
    for r in resps:
        por_asig[r.asignatura_id].append(r)
        por_grupo[r.grupo_id].append(r)
    asignaturas = []
    for a in db.scalars(
        select(Asignatura).where(Asignatura.programa_id.in_(ids)).order_by(Asignatura.semestre, Asignatura.nombre)
    ):
        grupos = [g for g in a.grupos if not periodo or g.periodo == periodo]
        if periodo and not grupos:
            continue  # con filtro de periodo, solo asignaturas que tuvieron grupo en ese periodo
        rs = por_asig.get(a.id, [])
        logro = _logro(rs)
        asignaturas.append(LogroAsignatura(
            asignatura_id=a.id, nombre=a.nombre, codigo=a.codigo, logro=logro, respuestas=len(rs),
            estudiantes=len({r.usuario_id for r in rs}), semaforo=semaforo(logro),
            grupos=[
                LogroGrupo(
                    grupo_id=g.id, nombre=g.nombre, periodo=g.periodo, docente=g.docente.nombre,
                    logro=_logro(por_grupo.get(g.id, [])), respuestas=len(por_grupo.get(g.id, [])),
                    estudiantes=len({r.usuario_id for r in por_grupo.get(g.id, [])}),
                    semaforo=semaforo(_logro(por_grupo.get(g.id, []))),
                )
                for g in sorted(grupos, key=lambda g: (g.periodo, g.nombre), reverse=False)
            ],
        ))

    # --- Tendencia semanal ---
    por_semana: dict[str, list[Resp]] = defaultdict(list)
    for r in resps:
        por_semana[_lunes(r.fecha)].append(r)
    tendencia = [PuntoTendencia(semana=s, logro=_logro(rs) or 0.0, respuestas=len(rs)) for s, rs in sorted(por_semana.items())]

    nombre = consultados[0].nombre if len(consultados) == 1 else "Todos los programas"
    return CoordinacionOut(
        programas=[ProgramaBasico(id=p.id, nombre=p.nombre) for p in disponibles],
        programa_id=consultados[0].id if programa_id is not None or len(consultados) == 1 else None,
        programa_nombre=nombre,
        periodo=periodo or None,
        periodos=periodos_disponibles(db, ids),
        logro_global=_logro(resps),
        respuestas=len(resps),
        estudiantes=len({r.usuario_id for r in resps}),
        ras=ras,
        bloom=bloom,
        asignaturas=asignaturas,
        tendencia=tendencia,
    )
