"""Notificaciones en la app: creación (sin duplicados) y generación diferida de las que dependen del tiempo."""
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos import Cuestionario, Grupo, Matricula, Notificacion, Repaso, Usuario, ahora, como_utc

# Las alertas tempranas se calculan al vuelo (cuestan varias consultas): como mucho una vez cada tanto por docente
INTERVALO_ALERTAS_S = 120
_ultimo_calculo_alertas: dict[int, float] = {}


def notificar(db: Session, usuario_id: int, tipo: str, titulo: str, mensaje: str = "", enlace: str = "",
              clave: str | None = None) -> Notificacion | None:
    """Crea una notificación sin hacer commit. Si ya existe una con la misma `clave` para el usuario, no hace nada."""
    if clave and db.scalar(
        select(Notificacion.id).where(Notificacion.usuario_id == usuario_id, Notificacion.clave == clave)
    ):
        return None
    n = Notificacion(usuario_id=usuario_id, tipo=tipo, titulo=titulo[:150], mensaje=mensaje, enlace=enlace[:200], clave=clave)
    db.add(n)
    db.flush()
    return n


def notificar_publicacion(db: Session, c: Cuestionario) -> int:
    """Avisa a los matriculados del grupo de que el cuestionario fue publicado (una sola vez por cuestionario)."""
    if not c.publicado or c.grupo_id is None:
        return 0
    grupo = db.get(Grupo, c.grupo_id)
    ids = db.scalars(select(Matricula.estudiante_id).where(Matricula.grupo_id == c.grupo_id)).all()
    nuevas = 0
    for uid in ids:
        if notificar(db, uid, "publicado", "Nuevo cuestionario publicado",
                     f"«{c.titulo}» está disponible en {grupo.nombre if grupo else 'tu grupo'}.",
                     f"/cuestionarios/{c.id}", clave=f"pub:{c.id}"):
            nuevas += 1
    return nuevas


def generar_pendientes(db: Session, usuario: Usuario) -> None:
    """Genera al consultar las notificaciones que dependen del paso del tiempo (repasos vencidos, alertas)."""
    ahora_ = ahora()
    repasos = db.scalars(
        select(Repaso).where(Repaso.usuario_id == usuario.id, Repaso.completado_intento_id.is_(None))
    ).all()
    for r in repasos:
        if como_utc(r.disponible_desde) <= ahora_:
            c = db.get(Cuestionario, r.cuestionario_id)
            if c is not None:
                notificar(db, usuario.id, "repaso", "Repaso disponible",
                          f"Ya puedes hacer el repaso diferido de «{c.titulo}».",
                          f"/cuestionarios/{c.id}", clave=f"repaso:{r.id}")

    if usuario.rol == "docente":
        ahora_s = time.monotonic()
        if ahora_s - _ultimo_calculo_alertas.get(usuario.id, -1e9) >= INTERVALO_ALERTAS_S:
            _ultimo_calculo_alertas[usuario.id] = ahora_s
            from app.services.alertas import calcular_alertas  # evita ciclos de importación

            grupos = db.scalars(select(Grupo).where(Grupo.docente_id == usuario.id)).all()
            for a in calcular_alertas(db, list(grupos)):
                motivos = ",".join(sorted(m.codigo for m in a.motivos))
                notificar(db, usuario.id, "alerta", f"Alerta temprana: {a.nombre}",
                          f"{a.nombre} ({a.grupo}): " + "; ".join(m.texto for m in a.motivos),
                          "/panel", clave=f"alerta:{a.grupo_id}:{a.estudiante_id}:{motivos}")
    db.commit()
