"""Encuesta de usabilidad SUS: respuesta del usuario y resumen anónimo para docentes."""
import csv
import io
import json
import statistics

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import RespuestaSUS, Usuario, ahora
from app.schemas_api import SusIn, SusOut, SusResumen
from app.seguridad import requiere_docente, usuario_actual
from app.services.sus import CATEGORIAS, calcular_puntaje, interpretar

router = APIRouter(prefix="/api/sus", tags=["sus"])


def _salida(r: RespuestaSUS) -> SusOut:
    return SusOut(
        respuestas=json.loads(r.respuestas_json),
        puntaje=r.puntaje_sus,
        interpretacion=interpretar(r.puntaje_sus),
        comentario=r.comentario,
        creado_en=r.creado_en,
    )


@router.post("", response_model=SusOut)
def responder(datos: SusIn, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Guarda la respuesta; si el usuario ya había respondido, la actualiza."""
    puntaje = calcular_puntaje(datos.respuestas)
    r = db.scalar(select(RespuestaSUS).where(RespuestaSUS.usuario_id == usuario.id))
    if r is None:
        r = RespuestaSUS(usuario_id=usuario.id)
        db.add(r)
    r.respuestas_json = json.dumps(datos.respuestas)
    r.puntaje_sus = puntaje
    r.comentario = datos.comentario
    r.creado_en = ahora()
    db.commit()
    return _salida(r)


@router.get("/mia", response_model=SusOut | None)
def mia(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    r = db.scalar(select(RespuestaSUS).where(RespuestaSUS.usuario_id == usuario.id))
    # 200 con null (no 404): no tener respuesta es un estado normal y no debe ensuciar la consola del navegador.
    return None if r is None else _salida(r)


@router.get("/resumen", response_model=SusResumen)
def resumen(_: Usuario = Depends(requiere_docente), db: Session = Depends(get_db)):
    filas = db.scalars(select(RespuestaSUS)).all()
    distribucion = {c: 0 for c in CATEGORIAS}
    if not filas:
        return SusResumen(n=0, distribucion=distribucion, promedio_por_item=[0.0] * 10)
    puntajes = [f.puntaje_sus for f in filas]
    for p in puntajes:
        distribucion[interpretar(p)] += 1
    matriz = [json.loads(f.respuestas_json) for f in filas]
    promedio = statistics.fmean(puntajes)
    return SusResumen(
        n=len(filas),
        promedio=round(promedio, 1),
        # Desviación estándar muestral (n-1); con una sola respuesta es 0
        desviacion=round(statistics.stdev(puntajes), 1) if len(puntajes) > 1 else 0.0,
        minimo=min(puntajes),
        maximo=max(puntajes),
        interpretacion_promedio=interpretar(promedio),
        distribucion=distribucion,
        promedio_por_item=[round(statistics.fmean(m[i] for m in matriz), 2) for i in range(10)],
    )


def _celda_segura(valor: str) -> str:
    """Evita la inyección de fórmulas al abrir el CSV en Excel."""
    return "'" + valor if valor[:1] in ("=", "+", "-", "@") else valor


@router.get("/resumen.csv")
def resumen_csv(_: Usuario = Depends(requiere_docente), db: Session = Depends(get_db)):
    """CSV anónimo (sin nombre ni correo, solo un id secuencial y el rol) de quienes aceptaron participar en el estudio."""
    filas = db.execute(
        select(RespuestaSUS, Usuario.rol)
        .join(Usuario, Usuario.id == RespuestaSUS.usuario_id)
        .where(Usuario.consentimiento_investigacion.is_(True))
        .order_by(RespuestaSUS.id)
    ).all()
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(["Id", "Rol"] + [f"P{i}" for i in range(1, 11)] + ["Puntaje SUS", "Interpretación", "Comentario", "Fecha (UTC)"])
    for n, (r, rol) in enumerate(filas, start=1):
        fecha = r.creado_en.strftime("%Y-%m-%d %H:%M")
        w.writerow(
            [n, rol, *json.loads(r.respuestas_json), r.puntaje_sus, interpretar(r.puntaje_sus),
             _celda_segura(r.comentario or ""), fecha]
        )
    contenido = "﻿" + salida.getvalue()  # BOM para que Excel muestre bien las tildes
    return Response(
        content=contenido.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="encuesta_sus.csv"'},
    )
