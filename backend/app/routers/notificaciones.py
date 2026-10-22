"""Notificaciones en la app: listado paginado, contador de no leídas y marcado como leídas."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Notificacion, Usuario
from app.schemas_api import ContadorNotificaciones, NotificacionesPagina, NotificacionOut
from app.seguridad import usuario_actual
from app.services.notificaciones import generar_pendientes

router = APIRouter(prefix="/api/notificaciones", tags=["notificaciones"])


def _no_leidas(db: Session, usuario_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Notificacion).where(Notificacion.usuario_id == usuario_id, Notificacion.leida.is_(False))
    ) or 0


@router.get("", response_model=NotificacionesPagina)
def listar(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=50),
    solo_no_leidas: bool = False,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
):
    generar_pendientes(db, usuario)
    filtro = [Notificacion.usuario_id == usuario.id]
    if solo_no_leidas:
        filtro.append(Notificacion.leida.is_(False))
    total = db.scalar(select(func.count()).select_from(Notificacion).where(*filtro)) or 0
    filas = db.scalars(
        select(Notificacion).where(*filtro).order_by(Notificacion.creada_en.desc(), Notificacion.id.desc())
        .offset((pagina - 1) * por_pagina).limit(por_pagina)
    ).all()
    return NotificacionesPagina(
        items=[NotificacionOut.model_validate(n, from_attributes=True) for n in filas],
        total=total, pagina=pagina, por_pagina=por_pagina, no_leidas=_no_leidas(db, usuario.id),
    )


@router.get("/no-leidas", response_model=ContadorNotificaciones)
def contador(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    generar_pendientes(db, usuario)
    return ContadorNotificaciones(no_leidas=_no_leidas(db, usuario.id))


@router.post("/leer-todas", response_model=ContadorNotificaciones)
def leer_todas(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    db.execute(update(Notificacion).where(Notificacion.usuario_id == usuario.id, Notificacion.leida.is_(False)).values(leida=True))
    db.commit()
    return ContadorNotificaciones(no_leidas=0)


@router.post("/{notificacion_id}/leer", response_model=ContadorNotificaciones)
def leer(notificacion_id: int, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    n = db.get(Notificacion, notificacion_id)
    if n is None or n.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    n.leida = True
    db.commit()
    return ContadorNotificaciones(no_leidas=_no_leidas(db, usuario.id))
