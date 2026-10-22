"""Procesamiento de videos: transcripción + generación con IA, guardado en BD."""
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, get_db
from app.modelos import Cuestionario, Pregunta, Tarea, Usuario, Video, ahora, como_utc
from app.schemas import Transcripcion
from app.schemas_api import ProcesarIn, TareaOut
from app.seguridad import usuario_actual
from app.services.ia import generar_con_respaldo
from app.services.transcripcion import identificar_video, obtener_transcripcion, transcribir_subida

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["procesar"])

EXTENSIONES_PERMITIDAS = {"mp4", "webm", "mov", "mkv", "mp3", "wav", "m4a", "ogg"}
CARPETA_SUBIDAS = Path(__file__).resolve().parents[2] / "subidas"


def _mensaje_amigable(e: Exception) -> str:
    texto = str(e)
    if isinstance(e, RuntimeError) and texto:
        return texto
    bajo = texto.lower()
    if "not a bot" in bajo or "429" in bajo or "too many requests" in bajo or "ipblocked" in bajo or "requestblocked" in bajo:
        return (
            "YouTube bloqueó temporalmente las descargas desde esta conexión (demasiadas solicitudes). "
            "Sube el video como archivo en la pestaña \"Subir archivo\", espera unas horas, "
            "o configura YOUTUBE_COOKIES en backend/.env (ver docs/DESPLIEGUE.md)."
        )
    if "drm" in bajo:
        return "El video tiene protección (DRM) y no se puede descargar. Prueba con otro video o sube el archivo."
    if "only works when logged-in" in bajo or "unauthorized" in bajo or "password" in bajo:
        return "El video de Vimeo es privado o requiere iniciar sesión. Usa un video público o no listado (con enlace completo)."
    if "private video" in bajo or "video unavailable" in bajo or "members-only" in bajo:
        return "El video es privado, no está disponible o es solo para miembros. Prueba con un video público."
    return f"No se pudo procesar el video ({type(e).__name__}). Intenta con otro video."


def _generar_y_guardar(db: Session, tarea: Tarea, video: Video, transcripcion: Transcripcion) -> None:
    """Paso común: IA -> Cuestionario con preguntas -> tarea lista."""
    tarea.estado = "generando"
    tarea.mensaje = "Generando resumen y cuestionario con IA…"
    db.commit()
    resultado, proveedor = generar_con_respaldo(transcripcion.texto_con_tiempos(), tarea.num_preguntas)

    cuestionario = Cuestionario(
        video_id=video.id,
        creador_id=tarea.usuario_id,
        titulo=resultado.titulo,
        resumen=resultado.resumen,
        ideas_clave_json=json.dumps(resultado.ideas_clave, ensure_ascii=False),
        proveedor_ia=proveedor,
        num_preguntas=len(resultado.preguntas),
        segundos_generacion=max(0, int((ahora() - como_utc(tarea.creado_en)).total_seconds())),
        preguntas=[
            Pregunta(
                orden=i,
                tipo=p.tipo,
                enunciado=p.enunciado,
                opciones_json=json.dumps(p.opciones, ensure_ascii=False),
                respuesta_correcta=p.respuesta_correcta,
                explicacion=p.explicacion,
                marca_tiempo=p.marca_tiempo,
                nivel_bloom=p.nivel_bloom,
            )
            for i, p in enumerate(resultado.preguntas)
        ],
    )
    db.add(cuestionario)
    db.flush()
    tarea.proveedor_ia = proveedor
    tarea.cuestionario_id = cuestionario.id
    tarea.estado = "listo"
    tarea.mensaje = "¡Listo!"
    db.commit()


def _ejecutar(tarea_id: str) -> None:
    """Corre en segundo plano con su PROPIA sesión de BD."""
    db = SessionLocal()
    try:
        tarea = db.get(Tarea, tarea_id)
        if tarea is None:
            return
        try:
            plataforma, video_id = identificar_video(tarea.url)
            video = db.scalar(
                select(Video).where(Video.plataforma == plataforma, Video.video_externo_id == video_id)
            )

            tarea.estado = "transcribiendo"
            tarea.mensaje = "Obteniendo la transcripción del video…"
            db.commit()

            if video:
                log.info("Caché de transcripción: reutilizando video %s:%s", plataforma, video_id)
                transcripcion = Transcripcion.model_validate_json(video.transcripcion_json)
                tarea.mensaje = "Transcripción reutilizada desde la caché."
            else:
                transcripcion = obtener_transcripcion(tarea.url)
                video = Video(
                    youtube_id=video_id if plataforma == "youtube" else None,
                    plataforma=plataforma,
                    video_externo_id=video_id,
                    url=tarea.url,
                    fuente_transcripcion=transcripcion.fuente,
                    transcripcion_json=transcripcion.model_dump_json(),
                )
                db.add(video)
                db.commit()
            tarea.fuente_transcripcion = video.fuente_transcripcion

            _generar_y_guardar(db, tarea, video, transcripcion)
        except Exception as e:
            log.exception("Error procesando la tarea %s", tarea_id)
            db.rollback()
            tarea = db.get(Tarea, tarea_id)
            if tarea:
                tarea.estado = "error"
                tarea.mensaje = _mensaje_amigable(e)
                db.commit()
    finally:
        db.close()


def _ejecutar_archivo(tarea_id: str) -> None:
    """Procesa un archivo subido: ffmpeg -> Whisper -> IA. Corre en segundo plano."""
    db = SessionLocal()
    try:
        tarea = db.get(Tarea, tarea_id)
        if tarea is None:
            return
        try:
            ruta = CARPETA_SUBIDAS / (tarea.archivo or "")
            if not tarea.archivo or not ruta.is_file():
                raise RuntimeError("No se encontró el archivo subido. Vuelve a subirlo.")
            tarea.estado = "transcribiendo"
            tarea.mensaje = "Extrayendo el audio y transcribiendo…"
            db.commit()

            transcripcion = transcribir_subida(ruta)
            video = Video(
                youtube_id=None,
                plataforma="archivo",
                url=tarea.url,
                archivo=tarea.archivo,
                titulo_original=tarea.url.removeprefix("archivo:")[:300],
                fuente_transcripcion=transcripcion.fuente,
                transcripcion_json=transcripcion.model_dump_json(),
            )
            db.add(video)
            db.commit()
            tarea.fuente_transcripcion = video.fuente_transcripcion
            _generar_y_guardar(db, tarea, video, transcripcion)
        except Exception as e:
            log.exception("Error procesando el archivo de la tarea %s", tarea_id)
            db.rollback()
            tarea = db.get(Tarea, tarea_id)
            if tarea:
                tarea.estado = "error"
                tarea.mensaje = _mensaje_amigable(e)
                db.commit()
    finally:
        db.close()


def _verificar_limite_diario(db: Session, usuario: Usuario) -> None:
    desde = datetime.now(timezone.utc) - timedelta(days=1)
    usadas = db.scalar(
        select(func.count()).select_from(Tarea).where(Tarea.usuario_id == usuario.id, Tarea.creado_en >= desde)
    )
    if usadas >= settings.limite_diario_procesamientos:
        raise HTTPException(
            status_code=429,
            detail=f"Alcanzaste el límite de {settings.limite_diario_procesamientos} videos procesados en 24 horas. Intenta más tarde.",
        )


@router.post("/procesar/archivo", response_model=TareaOut)
async def procesar_archivo(
    segundo_plano: BackgroundTasks,
    archivo: UploadFile = File(...),
    num_preguntas: int = Form(default=8, ge=3, le=20),
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    nombre_original = Path(archivo.filename or "").name
    ext = nombre_original.rsplit(".", 1)[-1].lower() if "." in nombre_original else ""
    if ext not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail="Formato no permitido. Usa: " + ", ".join(sorted(EXTENSIONES_PERMITIDAS)) + ".",
        )
    _verificar_limite_diario(db, usuario)

    limite = settings.max_subida_mb * 1024 * 1024
    CARPETA_SUBIDAS.mkdir(exist_ok=True)
    guardado = f"{uuid.uuid4().hex}.{ext}"
    destino = CARPETA_SUBIDAS / guardado
    total = 0
    try:
        with destino.open("wb") as f:
            while trozo := await archivo.read(1024 * 1024):
                total += len(trozo)
                if total > limite:
                    raise HTTPException(
                        status_code=413,
                        detail=f"El archivo supera el límite de {settings.max_subida_mb} MB.",
                    )
                f.write(trozo)
        if total == 0:
            raise HTTPException(status_code=400, detail="El archivo está vacío.")
    except BaseException:
        destino.unlink(missing_ok=True)
        raise

    tarea = Tarea(
        usuario_id=usuario.id,
        url=f"archivo:{nombre_original}"[:500],
        archivo=guardado,
        num_preguntas=num_preguntas,
        mensaje="En cola…",
    )
    db.add(tarea)
    db.commit()
    segundo_plano.add_task(_ejecutar_archivo, tarea.id)
    return tarea


@router.post("/procesar", response_model=TareaOut)
def procesar(
    datos: ProcesarIn,
    segundo_plano: BackgroundTasks,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    url = str(datos.url)
    try:
        identificar_video(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _verificar_limite_diario(db, usuario)

    tarea = Tarea(usuario_id=usuario.id, url=url, num_preguntas=datos.num_preguntas, mensaje="En cola…")
    db.add(tarea)
    db.commit()
    segundo_plano.add_task(_ejecutar, tarea.id)
    return tarea


@router.get("/tareas/{tarea_id}", response_model=TareaOut)
def obtener_tarea(tarea_id: str, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    tarea = db.get(Tarea, tarea_id)
    if not tarea or tarea.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea
