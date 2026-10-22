"""Consulta y borrado de cuestionarios."""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Cuestionario, Intento, Tarea, Usuario, Video
from app.routers import procesar
from app.schemas_api import CuestionarioDetalle, CuestionarioResumen, PreguntaOut, RepasoEstado
from app.seguridad import usuario_actual
from app.services.repasos import esta_vencido, repaso_pendiente
from app.services.transcripcion import hash_vimeo

router = APIRouter(prefix="/api/cuestionarios", tags=["cuestionarios"])


def cuestionario_visible(db: Session, cuestionario_id: int, usuario: Usuario) -> Cuestionario:
    """Devuelve el cuestionario si el usuario es el creador o si está publicado."""
    c = db.get(Cuestionario, cuestionario_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Cuestionario no encontrado.")
    if c.creador_id != usuario.id and not c.publicado:
        raise HTTPException(status_code=403, detail="Este cuestionario no está disponible para ti.")
    return c


def _tipo_medio(video: Video) -> str:
    if video.archivo:
        return "audio" if video.archivo.rsplit(".", 1)[-1].lower() in ("mp3", "wav", "m4a", "ogg") else "video"
    return "vimeo" if video.plataforma == "vimeo" else "youtube"


@router.get("", response_model=list[CuestionarioResumen])
def listar(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Los propios (propio=True) y los ajenos publicados en los que tengo intentos (propio=False)."""
    propios = db.scalars(
        select(Cuestionario).where(Cuestionario.creador_id == usuario.id).order_by(Cuestionario.creado_en.desc())
    ).all()
    todos_intentos = db.scalars(select(Intento).where(Intento.usuario_id == usuario.id)).all()
    mejores: dict[int, Intento] = {}
    for i in todos_intentos:
        if not i.finalizado:
            continue
        actual = mejores.get(i.cuestionario_id)
        if actual is None or i.puntaje > actual.puntaje:
            mejores[i.cuestionario_id] = i

    ids_propios = {c.id for c in propios}
    ids_unidos = {i.cuestionario_id for i in todos_intentos} - ids_propios
    unidos = (
        db.scalars(
            select(Cuestionario)
            .where(Cuestionario.id.in_(ids_unidos), Cuestionario.publicado.is_(True))
            .order_by(Cuestionario.creado_en.desc())
        ).all()
        if ids_unidos
        else []
    )
    nombres = {
        u.id: u.nombre
        for u in db.scalars(select(Usuario).where(Usuario.id.in_({c.creador_id for c in unidos}))).all()
    } if unidos else {}

    def resumen(c: Cuestionario, propio: bool) -> CuestionarioResumen:
        return CuestionarioResumen(
            id=c.id,
            titulo=c.titulo,
            creado_en=c.creado_en,
            num_preguntas=c.num_preguntas,
            youtube_id=c.video.youtube_id,
            plataforma=c.video.plataforma or "youtube",
            modo=c.modo or "aprendizaje",
            publicado=c.publicado,
            mejor_puntaje=mejores[c.id].puntaje if c.id in mejores else None,
            mejor_total=mejores[c.id].total if c.id in mejores else None,
            propio=propio,
            creador=None if propio else nombres.get(c.creador_id),
        )

    return [resumen(c, True) for c in propios] + [resumen(c, False) for c in unidos]


@router.get("/{cuestionario_id}", response_model=CuestionarioDetalle)
def detalle(cuestionario_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    c = cuestionario_visible(db, cuestionario_id, usuario)
    es_creador = c.creador_id == usuario.id
    modo = c.modo or "aprendizaje"
    # Grupo control: el estudiante solo ve el video y las preguntas (sin resumen, ideas clave ni marcas de tiempo)
    oculto = modo == "control" and not es_creador
    repaso = None
    if not es_creador:
        r = repaso_pendiente(db, usuario.id, c.id)
        if r is not None:
            repaso = RepasoEstado(disponible_desde=r.disponible_desde, vencido=esta_vencido(r))
    return CuestionarioDetalle(
        id=c.id,
        titulo=c.titulo,
        resumen="" if oculto else c.resumen,
        ideas_clave=[] if oculto else json.loads(c.ideas_clave_json),
        proveedor_ia=c.proveedor_ia,
        num_preguntas=c.num_preguntas,
        publicado=c.publicado,
        codigo_compartir=c.codigo_compartir if es_creador else None,
        es_creador=es_creador,
        youtube_id=c.video.youtube_id,
        medio=_tipo_medio(c.video),
        video_externo_id=c.video.video_externo_id,
        vimeo_hash=hash_vimeo(c.video.url) if c.video.plataforma == "vimeo" else None,
        archivo_url=f"/api/medios/{c.video.archivo}" if c.video.archivo else None,
        url=c.video.url,
        creado_en=c.creado_en,
        modo=modo,
        repaso_dias=c.repaso_dias,
        repaso=repaso,
        segundos_edicion=c.segundos_edicion if es_creador else None,
        estimacion_manual_min=c.estimacion_manual_min if es_creador else None,
        publicado_en=c.publicado_en if es_creador else None,
        grupo_id=c.grupo_id,
        grupo_nombre=c.grupo.nombre if c.grupo else None,
        asignatura_nombre=c.grupo.asignatura.nombre if c.grupo else None,
        preguntas=[
            PreguntaOut(
                id=p.id,
                orden=p.orden,
                tipo=p.tipo,
                enunciado=p.enunciado,
                opciones=json.loads(p.opciones_json),
                marca_tiempo="" if oculto else p.marca_tiempo,
                respuesta_correcta=p.respuesta_correcta if es_creador else None,
                explicacion=p.explicacion if es_creador else None,
                ra_id=p.ra_id if es_creador else None,
                nivel_bloom=p.nivel_bloom if es_creador else None,
            )
            for p in c.preguntas
        ],
    )


def borrar_cuestionario(db: Session, c: Cuestionario) -> Path | None:
    """Elimina el cuestionario (con preguntas, intentos y repasos) sin hacer commit.

    Si su video era un archivo subido y nadie más lo usa, también borra el registro Video y devuelve la ruta del
    archivo para que quien llama lo elimine del disco después del commit.
    """
    video = c.video
    db.execute(update(Tarea).where(Tarea.cuestionario_id == c.id).values(cuestionario_id=None))
    db.delete(c)
    db.flush()

    archivo = video.archivo if video else None
    if archivo:
        otros_cuestionarios = db.scalar(
            select(func.count()).select_from(Cuestionario).where(Cuestionario.video_id == video.id)
        )
        otros_videos = db.scalar(
            select(func.count()).select_from(Video).where(Video.archivo == archivo, Video.id != video.id)
        )
        if not otros_cuestionarios and not otros_videos:
            db.delete(video)
            return procesar.CARPETA_SUBIDAS / Path(archivo).name
    return None


@router.delete("/{cuestionario_id}", status_code=204)
def eliminar(cuestionario_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    c = db.get(Cuestionario, cuestionario_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Cuestionario no encontrado.")
    if c.creador_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo el creador puede eliminar el cuestionario.")
    ruta = borrar_cuestionario(db, c)
    db.commit()
    if ruta:
        ruta.unlink(missing_ok=True)
