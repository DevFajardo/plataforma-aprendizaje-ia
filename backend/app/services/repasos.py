"""Repasos diferidos (post-test): consulta de repasos pendientes y vencidos."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos import Repaso, ahora, como_utc


def repaso_pendiente(db: Session, usuario_id: int, cuestionario_id: int) -> Repaso | None:
    """Repaso aún no completado del usuario en el cuestionario (vencido o no)."""
    return db.scalar(
        select(Repaso).where(
            Repaso.usuario_id == usuario_id,
            Repaso.cuestionario_id == cuestionario_id,
            Repaso.completado_intento_id.is_(None),
        )
    )


def esta_vencido(repaso: Repaso) -> bool:
    return como_utc(repaso.disponible_desde) <= ahora()
