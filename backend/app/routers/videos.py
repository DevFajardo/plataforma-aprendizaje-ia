"""Accesibilidad: subtítulos WebVTT y transcripción descargable del video de un cuestionario."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Cuestionario, Usuario, Video
from app.schemas import Transcripcion
from app.seguridad import usuario_actual
from app.services import subtitulos

router = APIRouter(prefix="/api/videos", tags=["videos"])


class SegmentoOut(BaseModel):
    inicio: float
    texto: str


class TranscripcionOut(BaseModel):
    idioma: str
    fuente: str
    segmentos: list[SegmentoOut]


def _transcripcion_visible(db: Session, video_id: int, usuario: Usuario) -> Transcripcion:
    """El usuario debe ser creador de un cuestionario con ese video o ver uno publicado."""
    video = db.get(Video, video_id)
    acceso = db.scalar(
        select(Cuestionario.id).where(
            Cuestionario.video_id == video_id,
            or_(Cuestionario.creador_id == usuario.id, Cuestionario.publicado.is_(True)),
        )
    )
    if video is None or acceso is None:
        raise HTTPException(status_code=404, detail="Video no encontrado.")
    return Transcripcion.model_validate_json(video.transcripcion_json)


@router.get("/{video_id}/subtitulos.vtt")
def subtitulos_vtt(video_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    t = _transcripcion_visible(db, video_id, usuario)
    return PlainTextResponse(subtitulos.a_vtt(t), media_type="text/vtt; charset=utf-8")


@router.get("/{video_id}/transcripcion.txt")
def transcripcion_txt(video_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    t = _transcripcion_visible(db, video_id, usuario)
    return PlainTextResponse(
        subtitulos.a_texto(t),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="transcripcion_{video_id}.txt"'},
    )


@router.get("/{video_id}/transcripcion", response_model=TranscripcionOut)
def transcripcion_json(video_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    t = _transcripcion_visible(db, video_id, usuario)
    return TranscripcionOut(
        idioma=t.idioma, fuente=t.fuente, segmentos=[SegmentoOut(inicio=s.inicio, texto=s.texto) for s in t.segmentos]
    )
