"""Estadísticas personales (estudiante) y de los cuestionarios publicados (docente)."""
import json
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Cuestionario, Intento, Pregunta, Usuario
from app.schemas_api import (
    EstadisticasDocente,
    EstadisticasOut,
    PuntoEvolucion,
    ResumenCuestionarioDocente,
    TemaReforzar,
    TiempoDocente,
)
from app.seguridad import usuario_actual

router = APIRouter(prefix="/api/estadisticas", tags=["estadisticas"])


def porcentaje(i: Intento) -> float:
    return round(100 * i.puntaje / i.total, 1) if i.total else 0.0


def _promedio(valores: list[float]) -> float | None:
    return round(sum(valores) / len(valores), 1) if valores else None


def _tiempo_docente(cuestionarios: list[Cuestionario]) -> TiempoDocente:
    """Tiempo con la herramienta (generación + edición) vs. estimación del tiempo manual, en minutos."""
    con_estimacion = [c for c in cuestionarios if c.estimacion_manual_min]
    if not con_estimacion:
        return TiempoDocente(cuestionarios_con_estimacion=0)
    herramienta = sum((c.segundos_generacion or 0) + (c.segundos_edicion or 0) for c in con_estimacion) / 60 / len(con_estimacion)
    manual = sum(c.estimacion_manual_min for c in con_estimacion) / len(con_estimacion)
    return TiempoDocente(
        cuestionarios_con_estimacion=len(con_estimacion),
        promedio_herramienta_min=round(herramienta, 1),
        promedio_manual_min=round(manual, 1),
        ahorro_pct=round(100 * (manual - herramienta) / manual, 1),
    )


@router.get("/yo", response_model=EstadisticasOut)
def estadisticas_yo(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    intentos = db.scalars(
        select(Intento)
        .where(Intento.usuario_id == usuario.id, Intento.finalizado.is_(True))
        .order_by(Intento.creado_en, Intento.id)
    ).all()
    porcentajes = [porcentaje(i) for i in intentos]

    propios = db.scalars(select(Cuestionario).where(Cuestionario.creador_id == usuario.id)).all()
    ids_propios = {c.id for c in propios}
    # Cuestionarios ajenos en los que el usuario tiene al menos un intento
    ids_unidos = {i.cuestionario_id for i in db.scalars(select(Intento).where(Intento.usuario_id == usuario.id))} - ids_propios

    titulos = {c.id: c.titulo for c in db.scalars(select(Cuestionario).where(Cuestionario.id.in_({i.cuestionario_id for i in intentos})))} if intentos else {}
    evolucion = [
        PuntoEvolucion(fecha=i.creado_en, porcentaje=p, cuestionario_titulo=titulos.get(i.cuestionario_id, ""))
        for i, p in list(zip(intentos, porcentajes))[-20:]
    ]

    # Preguntas más falladas (solo cerradas: correcta == False)
    fallos: Counter[int] = Counter()
    for i in intentos:
        for r in json.loads(i.respuestas_json):
            if r.get("correcta") is False:
                fallos[r["pregunta_id"]] += 1
    temas: list[TemaReforzar] = []
    for pid, n in fallos.most_common():
        p = db.get(Pregunta, pid)
        if p is None:  # la pregunta fue eliminada o el cuestionario borrado
            continue
        c = db.get(Cuestionario, p.cuestionario_id)
        temas.append(
            TemaReforzar(
                pregunta_id=p.id,
                enunciado=p.enunciado,
                cuestionario_id=p.cuestionario_id,
                cuestionario_titulo=c.titulo if c else "",
                fallos=n,
            )
        )
        if len(temas) == 5:
            break

    # Retención personal: diferido / inicial x 100 en cada cuestionario con ambos intentos, y su promedio
    primeros: dict[tuple[int, str], Intento] = {}
    for i in intentos:
        if i.tipo in ("inicial", "diferido"):
            primeros.setdefault((i.cuestionario_id, i.tipo), i)
    retenciones = [
        100 * porcentaje(primeros[(cid, "diferido")]) / porcentaje(inicial)
        for (cid, tipo), inicial in primeros.items()
        if tipo == "inicial" and (cid, "diferido") in primeros and porcentaje(inicial) > 0
    ]

    docente = None
    if usuario.rol == "docente":
        publicados = [c for c in propios if c.publicado]
        por_cuestionario: list[ResumenCuestionarioDocente] = []
        todos: list[float] = []
        estudiantes: set[int] = set()
        total_intentos = 0
        for c in publicados:
            # Los intentos del propio docente (pruebas) no cuentan como de estudiantes
            recibidos = [i for i in c.intentos if i.finalizado and i.usuario_id != usuario.id]
            ps = [porcentaje(i) for i in recibidos]
            todos += ps
            total_intentos += len(recibidos)
            estudiantes |= {i.usuario_id for i in recibidos}
            por_cuestionario.append(
                ResumenCuestionarioDocente(
                    id=c.id, titulo=c.titulo, intentos=len(recibidos), promedio=_promedio(ps),
                    codigo_compartir=c.codigo_compartir,
                )
            )
        docente = EstadisticasDocente(
            cuestionarios_publicados=len(publicados),
            estudiantes_unicos=len(estudiantes),
            intentos_recibidos=total_intentos,
            promedio_general=_promedio(todos),
            por_cuestionario=por_cuestionario,
            tiempo=_tiempo_docente(propios),
        )

    return EstadisticasOut(
        rol=usuario.rol,
        intentos_finalizados=len(intentos),
        promedio_porcentaje=_promedio(porcentajes),
        mejor_porcentaje=max(porcentajes) if porcentajes else None,
        retencion_promedio=_promedio(retenciones),
        cuestionarios_generados=len(propios),
        cuestionarios_unidos=len(ids_unidos),
        evolucion=evolucion,
        temas_a_reforzar=temas,
        docente=docente,
    )
