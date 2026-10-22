"""Tutor IA del video: «Pregúntale al video» (chat con citas de la transcripción)."""
import json
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.modelos import ConversacionTutor, Cuestionario, Intento, MensajeTutor, Usuario, Video, ahora
from app.routers.cuestionarios import cuestionario_visible
from app.schemas import Transcripcion
from app.schemas_s8 import CitaOut, MensajeTutorOut, PreguntaTutorIn, RespuestaTutorOut, TutorEstado
from app.seguridad import usuario_actual
from app.services import ia, tutor
from app.services.repasos import esta_vencido, repaso_pendiente

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cuestionarios", tags=["tutor"])


def _mensaje_out(m: MensajeTutor) -> MensajeTutorOut:
    return MensajeTutorOut(
        id=m.id, rol=m.rol, texto=m.texto, citas=[CitaOut(**c) for c in tutor.citas_de(m)], creado_en=m.creado_en
    )


def _intento_en_curso(db: Session, usuario: Usuario, c: Cuestionario) -> Intento | None:
    return db.scalar(
        select(Intento)
        .where(Intento.usuario_id == usuario.id, Intento.cuestionario_id == c.id, Intento.finalizado.is_(False))
        .order_by(Intento.id.desc())
    )


def motivo_bloqueo(db: Session, usuario: Usuario, c: Cuestionario) -> str:
    """Texto con el motivo por el que el tutor no está disponible ('' si lo está)."""
    if (c.modo or "aprendizaje") == "control":
        return "El tutor no está disponible en este cuestionario (grupo control)."
    en_curso = _intento_en_curso(db, usuario, c)
    if en_curso is not None and en_curso.tipo == "diferido":
        return "El tutor no está disponible durante el repaso diferido."
    repaso = repaso_pendiente(db, usuario.id, c.id) if c.creador_id != usuario.id else None
    if repaso is not None and esta_vencido(repaso):
        return "El tutor no está disponible mientras tengas pendiente el repaso diferido de este cuestionario."
    return ""


def enunciados_pendientes(db: Session, usuario: Usuario, c: Cuestionario) -> list[str]:
    """Enunciados (solo el texto) de las preguntas que el usuario aún no responde en su intento en curso."""
    intento = _intento_en_curso(db, usuario, c)
    if intento is None:
        return []
    respondidas = {r["pregunta_id"] for r in json.loads(intento.respuestas_json)}
    return [p.enunciado for p in c.preguntas if p.id not in respondidas]


def _mensajes_usados_hoy(db: Session, usuario: Usuario) -> int:
    desde = ahora() - timedelta(days=1)
    return db.scalar(
        select(func.count())
        .select_from(MensajeTutor)
        .join(ConversacionTutor, ConversacionTutor.id == MensajeTutor.conversacion_id)
        .where(ConversacionTutor.usuario_id == usuario.id, MensajeTutor.rol == "usuario", MensajeTutor.creado_en >= desde)
    ) or 0


def _conversacion_activa(db: Session, usuario: Usuario, c: Cuestionario) -> ConversacionTutor | None:
    return db.scalar(
        select(ConversacionTutor)
        .where(ConversacionTutor.usuario_id == usuario.id, ConversacionTutor.cuestionario_id == c.id)
        .order_by(ConversacionTutor.id.desc())
    )


@router.get("/{cuestionario_id}/tutor", response_model=TutorEstado)
def estado_tutor(cuestionario_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    c = cuestionario_visible(db, cuestionario_id, usuario)
    motivo = motivo_bloqueo(db, usuario, c)
    conv = _conversacion_activa(db, usuario, c)
    usados = _mensajes_usados_hoy(db, usuario)
    return TutorEstado(
        habilitado=not motivo,
        motivo=motivo,
        conversacion_id=conv.id if conv else None,
        mensajes=[_mensaje_out(m) for m in conv.mensajes] if conv else [],
        restantes=max(0, settings.limite_tutor_diario - usados),
        limite=settings.limite_tutor_diario,
        sugerencias=tutor.sugerencias_iniciales(json.loads(c.ideas_clave_json), c.titulo),
    )


@router.post("/{cuestionario_id}/tutor/nueva", response_model=TutorEstado, status_code=201)
def nueva_conversacion(cuestionario_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    c = cuestionario_visible(db, cuestionario_id, usuario)
    db.add(ConversacionTutor(usuario_id=usuario.id, cuestionario_id=c.id))
    db.commit()
    return estado_tutor(cuestionario_id, usuario, db)


@router.post("/{cuestionario_id}/tutor", response_model=RespuestaTutorOut)
def preguntar(
    cuestionario_id: int,
    datos: PreguntaTutorIn,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    c = cuestionario_visible(db, cuestionario_id, usuario)
    motivo = motivo_bloqueo(db, usuario, c)
    if motivo:
        raise HTTPException(status_code=403, detail=motivo)
    usados = _mensajes_usados_hoy(db, usuario)
    if usados >= settings.limite_tutor_diario:
        raise HTTPException(
            status_code=429,
            detail=f"Alcanzaste el límite de {settings.limite_tutor_diario} mensajes al tutor en 24 horas. Intenta más tarde.",
        )
    pregunta = datos.pregunta.strip()
    if not pregunta:
        raise HTTPException(status_code=422, detail="Escribe una pregunta.")

    video = db.get(Video, c.video_id)
    transcripcion = Transcripcion.model_validate_json(video.transcripcion_json)
    conv = _conversacion_activa(db, usuario, c)
    historial = tutor.historial_desde_mensajes(conv.mensajes) if conv else []
    prompt = tutor.construir_prompt(
        tutor.construir_contexto(transcripcion, pregunta), historial, pregunta, enunciados_pendientes(db, usuario, c)
    )
    try:
        respuesta, _proveedor = ia.ejecutar_con_respaldo(prompt, tutor.RespuestaTutor)
    except Exception:
        log.exception("El tutor IA no pudo responder")
        raise HTTPException(status_code=503, detail="El tutor no pudo responder ahora (la IA no está disponible). Inténtalo en un momento.")

    if conv is None:
        conv = ConversacionTutor(usuario_id=usuario.id, cuestionario_id=c.id)
        db.add(conv)
        db.flush()
    citas = tutor.validar_citas(respuesta.citas, transcripcion)
    m_usuario = MensajeTutor(conversacion_id=conv.id, rol="usuario", texto=pregunta)
    m_tutor = MensajeTutor(
        conversacion_id=conv.id, rol="tutor", texto=respuesta.texto.strip(), citas_json=json.dumps(citas, ensure_ascii=False)
    )
    db.add_all([m_usuario, m_tutor])
    db.commit()
    return RespuestaTutorOut(
        usuario=_mensaje_out(m_usuario), tutor=_mensaje_out(m_tutor), restantes=max(0, settings.limite_tutor_diario - usados - 1)
    )
