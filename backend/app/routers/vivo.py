"""Clase en vivo: sesiones, unión de participantes, WebSocket, sondeo HTTP de respaldo e historial."""
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Cuestionario, ParticipanteVivo, RespuestaVivo, SesionVivo, Usuario
from app.routers.docente import _celda_segura
from app.schemas_vivo import (
    AccionVivoIn,
    IniciarVivoIn,
    PreguntaHistorialVivo,
    RespuestaVivoIn,
    SesionHistorialVivo,
    SesionVivoOut,
    UnidoVivoOut,
    UnirseVivoIn,
)
from app.seguridad import decodificar_token, esquema, requiere_docente
from app.services import vivo

router = APIRouter(tags=["vivo"])


def _error(e: vivo.ErrorVivo) -> HTTPException:
    return HTTPException(status_code=e.codigo, detail=e.mensaje)


def _usuario_opcional(credenciales: HTTPAuthorizationCredentials | None, db: Session) -> Usuario | None:
    if credenciales is None:
        return None
    uid = decodificar_token(credenciales.credentials)
    return db.get(Usuario, uid) if uid is not None else None


def _cuestionario_propio(db: Session, cuestionario_id: int, docente: Usuario) -> Cuestionario:
    c = db.get(Cuestionario, cuestionario_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Cuestionario no encontrado.")
    if c.creador_id != docente.id:
        raise HTTPException(status_code=403, detail="Solo el creador del cuestionario puede hacer esto.")
    return c


def _sesion_propia(sesion_id: int, docente: Usuario, db: Session) -> SesionVivo:
    s = db.get(SesionVivo, sesion_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    if s.docente_id != docente.id:
        raise HTTPException(status_code=403, detail="Solo el docente que la creó controla esta sesión.")
    return s


def _salida(m: vivo.SesionMem) -> SesionVivoOut:
    return SesionVivoOut(id=m.id, cuestionario_id=m.cuestionario_id, titulo=m.titulo, pin=m.pin, estado=m.estado,
                         segundos_por_pregunta=m.segundos, total_preguntas=len(m.preguntas))


# ---------- Docente: crear y consultar sesiones ----------

@router.post("/api/cuestionarios/{cuestionario_id}/vivo", response_model=SesionVivoOut, status_code=201)
async def iniciar_clase(
    cuestionario_id: int,
    datos: IniciarVivoIn | None = None,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    c = _cuestionario_propio(db, cuestionario_id, docente)
    try:
        m = vivo.crear_sesion(c, docente, (datos or IniciarVivoIn()).segundos_por_pregunta)
    except vivo.ErrorVivo as e:
        raise _error(e) from e
    return _salida(m)


@router.get("/api/vivo/sesiones/{sesion_id}", response_model=SesionVivoOut)
async def obtener_sesion(sesion_id: int, docente: Usuario = Depends(requiere_docente), db: Session = Depends(get_db)):
    s = _sesion_propia(sesion_id, docente, db)
    m = vivo.obtener_por_id(sesion_id)
    if m is None:
        raise HTTPException(status_code=410, detail="Esta clase en vivo ya terminó o expiró.")
    assert m.docente_id == s.docente_id
    return _salida(m)


@router.post("/api/vivo/sesiones/{sesion_id}/accion", status_code=204)
async def accion(sesion_id: int, datos: AccionVivoIn, docente: Usuario = Depends(requiere_docente), db: Session = Depends(get_db)):
    """Controles del presentador por HTTP (respaldo cuando el WebSocket no funciona)."""
    _sesion_propia(sesion_id, docente, db)
    m = vivo.obtener_por_id(sesion_id)
    if m is None:
        raise HTTPException(status_code=410, detail="Esta clase en vivo ya terminó o expiró.")
    try:
        await vivo.accion_presentador(m, datos.accion)
    except vivo.ErrorVivo as e:
        raise _error(e) from e


# ---------- Participantes ----------

@router.post("/api/vivo/unirse", response_model=UnidoVivoOut)
async def unirse(
    datos: UnirseVivoIn,
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema),
    db: Session = Depends(get_db),
):
    """Sin cuenta: basta el PIN y un apodo. Con sesión iniciada, el participante queda vinculado a su usuario."""
    m = vivo.obtener(datos.pin)
    if m is None:
        raise HTTPException(status_code=404, detail="No hay una clase en vivo con ese PIN.")
    usuario = _usuario_opcional(credenciales, db)
    try:
        p = vivo.unirse(m, datos.apodo, usuario)
    except vivo.ErrorVivo as e:
        raise _error(e) from e
    await vivo.difundir(m)
    return UnidoVivoOut(pin=m.pin, apodo=p.apodo, token=p.token)


@router.get("/api/vivo/{pin}/estado")
async def estado(
    pin: str,
    participante: str | None = None,
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema),
    db: Session = Depends(get_db),
):
    """Sondeo de respaldo: participante (token) o presentador (JWT del docente dueño). Sin credenciales, datos mínimos."""
    m = vivo.obtener(pin)
    if m is None:
        raise HTTPException(status_code=404, detail="No hay una clase en vivo con ese PIN.")
    if participante:
        pid = m.tokens.get(participante)
        if pid is None:
            raise HTTPException(status_code=403, detail="Participante no reconocido en esta sesión.")
        return vivo.snapshot(m, "participante", pid)
    usuario = _usuario_opcional(credenciales, db)
    if usuario is not None and usuario.id == m.docente_id:
        return vivo.snapshot(m, "presentador")
    return {"tipo": "estado", "rol": "publico", "pin": m.pin, "titulo": m.titulo, "estado": m.estado,
            "num_participantes": len(m.apodos)}


@router.post("/api/vivo/{pin}/responder", status_code=204)
async def responder_http(pin: str, datos: RespuestaVivoIn):
    m = vivo.obtener(pin)
    if m is None:
        raise HTTPException(status_code=404, detail="No hay una clase en vivo con ese PIN.")
    pid = m.tokens.get(datos.token)
    if pid is None:
        raise HTTPException(status_code=403, detail="Participante no reconocido en esta sesión.")
    try:
        await vivo.responder(m, pid, datos.respuesta)
    except vivo.ErrorVivo as e:
        raise _error(e) from e


# ---------- WebSocket ----------

@router.websocket("/ws/vivo/{pin}")
async def ws_vivo(ws: WebSocket, pin: str, token: str | None = None, participante: str | None = None):
    """Presentador: `?token=<JWT del docente dueño>`. Participante: `?participante=<token secreto>`."""
    m = vivo.obtener(pin)
    if m is None:
        await ws.close(code=4404)
        return
    if token:
        if decodificar_token(token) != m.docente_id:
            await ws.close(code=4403)
            return
        rol, pid = "presentador", None
    elif participante and participante in m.tokens:
        rol, pid = "participante", m.tokens[participante]
    else:
        await ws.close(code=4401)
        return

    await ws.accept()
    m.conexiones[ws] = (rol, pid)
    try:
        await vivo.enviar(m, ws)
        while True:
            msg = await ws.receive_json()
            if not isinstance(msg, dict):
                continue
            accion_ws = msg.get("accion")
            try:
                if accion_ws == "ping":
                    await ws.send_json({"tipo": "pong"})
                elif rol == "presentador" and isinstance(accion_ws, str):
                    await vivo.accion_presentador(m, accion_ws)
                elif rol == "participante" and accion_ws == "responder" and pid is not None:
                    await vivo.responder(m, pid, str(msg.get("respuesta", "")))
                else:
                    await ws.send_json({"tipo": "error", "mensaje": "Acción no permitida."})
            except vivo.ErrorVivo as e:
                await ws.send_json({"tipo": "error", "mensaje": e.mensaje})
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        m.conexiones.pop(ws, None)


# ---------- Historial y CSV ----------

def _historial(db: Session, c: Cuestionario) -> list[SesionHistorialVivo]:
    sesiones = db.scalars(
        select(SesionVivo).where(SesionVivo.cuestionario_id == c.id).order_by(SesionVivo.creada_en.desc(), SesionVivo.id.desc())
    ).all()
    tipo = {p.id: p.tipo for p in c.preguntas}
    salida = []
    for s in sesiones:
        resp = db.scalars(select(RespuestaVivo).where(RespuestaVivo.sesion_id == s.id)).all()
        cerradas = [r for r in resp if r.correcta is not None]
        preguntas = []
        for p in c.preguntas:
            rp = [r for r in resp if r.pregunta_id == p.id]
            cp = [r for r in rp if r.correcta is not None]
            preguntas.append(PreguntaHistorialVivo(
                pregunta_id=p.id, orden=p.orden, enunciado=p.enunciado, tipo=tipo[p.id], respuestas=len(rp),
                porcentaje_acierto=round(100 * sum(1 for r in cp if r.correcta) / len(cp), 1) if cp else None,
            ))
        salida.append(SesionHistorialVivo(
            id=s.id, creada_en=s.creada_en, finalizada_en=s.finalizada_en, estado=s.estado, pin=s.pin,
            participantes=len(s.participantes),
            promedio_acierto=round(100 * sum(1 for r in cerradas if r.correcta) / len(cerradas), 1) if cerradas else None,
            preguntas=preguntas,
        ))
    return salida


@router.get("/api/cuestionarios/{cuestionario_id}/vivo", response_model=list[SesionHistorialVivo])
def historial(cuestionario_id: int, docente: Usuario = Depends(requiere_docente), db: Session = Depends(get_db)):
    return _historial(db, _cuestionario_propio(db, cuestionario_id, docente))


@router.get("/api/cuestionarios/{cuestionario_id}/vivo.csv")
def historial_csv(cuestionario_id: int, docente: Usuario = Depends(requiere_docente), db: Session = Depends(get_db)):
    c = _cuestionario_propio(db, cuestionario_id, docente)
    sesiones = _historial(db, c)
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(["Sesión", "Fecha (UTC)", "PIN", "Estado", "Participantes", "Promedio de acierto (%)"])
    for s in sesiones:
        w.writerow([s.id, s.creada_en.strftime("%Y-%m-%d %H:%M"), s.pin, s.estado, s.participantes,
                    s.promedio_acierto if s.promedio_acierto is not None else ""])
    w.writerow([])
    w.writerow(["Sesión", "Pregunta", "Enunciado", "Tipo", "Respuestas", "Acierto (%)"])
    for s in sesiones:
        for p in s.preguntas:
            w.writerow([s.id, p.orden, _celda_segura(p.enunciado), p.tipo, p.respuestas,
                        p.porcentaje_acierto if p.porcentaje_acierto is not None else ""])
    w.writerow([])
    w.writerow(["Sesión", "Apodo", "Nombre (si inició sesión)", "Puntos", "Posición", "Aciertos", "Respondidas"])
    for s in sesiones:
        partes = db.scalars(select(ParticipanteVivo).where(ParticipanteVivo.sesion_id == s.id)).all()
        resp = db.scalars(select(RespuestaVivo).where(RespuestaVivo.sesion_id == s.id)).all()
        for p in sorted(partes, key=lambda x: (-x.puntaje, x.apodo.lower())):
            mias = [r for r in resp if r.participante_id == p.id]
            usuario = db.get(Usuario, p.usuario_id) if p.usuario_id else None
            posicion = 1 + sum(1 for o in partes if o.puntaje > p.puntaje)
            w.writerow([s.id, _celda_segura(p.apodo), _celda_segura(usuario.nombre) if usuario else "", p.puntaje,
                        posicion, sum(1 for r in mias if r.correcta), len(mias)])
    contenido = "﻿" + salida.getvalue()  # BOM para que Excel muestre bien las tildes
    return Response(
        content=contenido.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="clases_en_vivo_{cuestionario_id}.csv"'},
    )
