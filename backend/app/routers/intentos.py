"""Intentos de cuestionario: calificación en servidor, repasos diferidos e historial."""
import json
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Cuestionario, Intento, Repaso, Usuario, ahora
from app.routers.cuestionarios import cuestionario_visible
from app.schemas_api import (
    IntentoCreado,
    IntentoHistorial,
    IntentoResumen,
    RepasoOut,
    RespuestaIn,
    RespuestaOut,
    RevisionPregunta,
)
from app.seguridad import usuario_actual
from app.services.repasos import esta_vencido, repaso_pendiente

router = APIRouter(prefix="/api", tags=["intentos"])


def _normalizar(texto: str) -> str:
    return " ".join(texto.strip().lower().split())


def _con_feedback(intento: Intento) -> bool:
    """Los repasos diferidos y el grupo control no reciben retroalimentación por pregunta."""
    return intento.tipo != "diferido" and intento.cuestionario.modo != "control"


def _resumen(i: Intento) -> IntentoResumen:
    return IntentoResumen(
        id=i.id,
        cuestionario_id=i.cuestionario_id,
        puntaje=i.puntaje,
        total=i.total,
        porcentaje=round(100 * i.puntaje / i.total, 1) if i.total else 0.0,
        finalizado=i.finalizado,
        creado_en=i.creado_en,
        tipo=i.tipo or "inicial",
    )


def _revision(intento: Intento) -> list[RevisionPregunta]:
    """Respuestas del estudiante junto a las correctas (solo se entrega al finalizar un repaso diferido)."""
    dadas = {r["pregunta_id"]: r for r in json.loads(intento.respuestas_json)}
    salida = []
    for p in intento.cuestionario.preguntas:
        r = dadas.get(p.id)
        salida.append(
            RevisionPregunta(
                pregunta_id=p.id,
                enunciado=p.enunciado,
                respuesta=r["respuesta"] if r else "",
                correcta=r["correcta"] if r else None,
                respuesta_correcta=p.respuesta_correcta,
                explicacion=p.explicacion,
                marca_tiempo=p.marca_tiempo,
            )
        )
    return salida


def _intento_propio(db: Session, intento_id: int, usuario: Usuario) -> Intento:
    intento = db.get(Intento, intento_id)
    if intento is None or intento.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Intento no encontrado.")
    return intento


def _tipo_no_diferido(db: Session, usuario_id: int, cuestionario_id: int, excluir_id: int | None = None) -> str:
    """"inicial" si es el primer intento finalizado (no diferido) del usuario en el cuestionario; si no, "practica"."""
    consulta = select(func.count()).select_from(Intento).where(
        Intento.usuario_id == usuario_id,
        Intento.cuestionario_id == cuestionario_id,
        Intento.finalizado.is_(True),
        Intento.tipo != "diferido",
    )
    if excluir_id is not None:
        consulta = consulta.where(Intento.id != excluir_id)
    return "practica" if db.scalar(consulta) else "inicial"


@router.post("/cuestionarios/{cuestionario_id}/intentos", response_model=IntentoCreado, status_code=201)
def crear_intento(cuestionario_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    c = cuestionario_visible(db, cuestionario_id, usuario)
    repaso = repaso_pendiente(db, usuario.id, c.id)
    if repaso is not None and esta_vencido(repaso):
        tipo = "diferido"
    else:
        tipo = _tipo_no_diferido(db, usuario.id, c.id)
    intento = Intento(usuario_id=usuario.id, cuestionario_id=c.id, tipo=tipo)
    db.add(intento)
    db.commit()
    return IntentoCreado(
        id=intento.id,
        cuestionario_id=c.id,
        tipo=tipo,
        con_feedback=tipo != "diferido" and c.modo != "control",
    )


@router.post("/intentos/{intento_id}/responder", response_model=RespuestaOut)
def responder(intento_id: int, datos: RespuestaIn, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    intento = _intento_propio(db, intento_id, usuario)
    if intento.finalizado:
        raise HTTPException(status_code=409, detail="Este intento ya fue finalizado.")
    pregunta = next((p for p in intento.cuestionario.preguntas if p.id == datos.pregunta_id), None)
    if pregunta is None:
        raise HTTPException(status_code=404, detail="La pregunta no pertenece a este cuestionario.")

    respuestas = json.loads(intento.respuestas_json)
    if any(r["pregunta_id"] == pregunta.id for r in respuestas):
        raise HTTPException(status_code=409, detail="Ya respondiste esta pregunta en este intento.")

    if pregunta.tipo == "abierta":
        correcta = None
    else:
        correcta = _normalizar(datos.respuesta) == _normalizar(pregunta.respuesta_correcta)
    respuestas.append({"pregunta_id": pregunta.id, "respuesta": datos.respuesta, "correcta": correcta})
    intento.respuestas_json = json.dumps(respuestas, ensure_ascii=False)
    db.commit()
    if not _con_feedback(intento):
        return RespuestaOut(registrada=True, con_feedback=False)
    return RespuestaOut(
        correcta=correcta,
        respuesta_correcta=pregunta.respuesta_correcta,
        explicacion=pregunta.explicacion,
        marca_tiempo=pregunta.marca_tiempo,
    )


@router.post("/intentos/{intento_id}/finalizar", response_model=IntentoResumen)
def finalizar(intento_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    intento = _intento_propio(db, intento_id, usuario)
    c = intento.cuestionario
    if not intento.finalizado:
        respuestas = json.loads(intento.respuestas_json)
        intento.puntaje = sum(1 for r in respuestas if r["correcta"] is True)
        intento.total = sum(1 for p in c.preguntas if p.tipo != "abierta")
        intento.finalizado = True

        if intento.tipo == "diferido":
            repaso = repaso_pendiente(db, usuario.id, c.id)
            if repaso is not None:
                repaso.completado_intento_id = intento.id
            else:  # otro intento diferido ya completó el repaso: este cuenta como práctica
                intento.tipo = "practica"
        else:
            intento.tipo = _tipo_no_diferido(db, usuario.id, c.id, excluir_id=intento.id)
            ya_tiene_repaso = db.scalar(
                select(Repaso.id).where(Repaso.usuario_id == usuario.id, Repaso.cuestionario_id == c.id)
            )
            # El creador no recibe repasos: sus intentos son pruebas del cuestionario
            if intento.tipo == "inicial" and c.repaso_dias and usuario.id != c.creador_id and not ya_tiene_repaso:
                db.add(
                    Repaso(
                        usuario_id=usuario.id,
                        cuestionario_id=c.id,
                        disponible_desde=ahora() + timedelta(days=c.repaso_dias),
                    )
                )
        db.commit()

    resumen = _resumen(intento)
    if intento.tipo == "diferido" and c.modo != "control":
        resumen.revision = _revision(intento)
    pendiente = repaso_pendiente(db, usuario.id, c.id)
    if intento.tipo == "inicial" and pendiente is not None:
        resumen.repaso_disponible_desde = pendiente.disponible_desde
    return resumen


@router.get("/intentos", response_model=list[IntentoHistorial])
def historial(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    filas = db.execute(
        select(Intento, Cuestionario.titulo)
        .join(Cuestionario, Cuestionario.id == Intento.cuestionario_id)
        .where(Intento.usuario_id == usuario.id, Intento.finalizado.is_(True))
        .order_by(Intento.creado_en.desc())
    ).all()
    return [IntentoHistorial(**_resumen(i).model_dump(), cuestionario_titulo=titulo) for i, titulo in filas]


@router.get("/repasos", response_model=list[RepasoOut])
def repasos_pendientes(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Repasos del usuario aún no completados: vencidos (listos para hacer) y próximos (con su fecha)."""
    filas = db.execute(
        select(Repaso, Cuestionario)
        .join(Cuestionario, Cuestionario.id == Repaso.cuestionario_id)
        .where(Repaso.usuario_id == usuario.id, Repaso.completado_intento_id.is_(None))
        .order_by(Repaso.disponible_desde)
    ).all()
    return [
        RepasoOut(
            id=r.id,
            cuestionario_id=c.id,
            cuestionario_titulo=c.titulo,
            disponible_desde=r.disponible_desde,
            vencido=esta_vencido(r),
        )
        for r, c in filas
        if c.publicado or c.creador_id == usuario.id
    ]
