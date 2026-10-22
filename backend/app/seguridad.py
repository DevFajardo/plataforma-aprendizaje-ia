"""Contraseñas (bcrypt), tokens JWT y dependencias de autenticación."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.modelos import Usuario

ALGORITMO = "HS256"
esquema = HTTPBearer(auto_error=False)


def hashear_password(password: str) -> str:
    # bcrypt solo admite 72 bytes
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hash_guardado.encode("utf-8"))
    except ValueError:
        return False


def _clave() -> str:
    if not settings.secret_key:
        raise RuntimeError("Falta SECRET_KEY en el archivo .env")
    return settings.secret_key


def crear_token(usuario_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=settings.token_expira_horas)
    return jwt.encode({"sub": str(usuario_id), "exp": exp}, _clave(), algorithm=ALGORITMO)


def decodificar_token(token: str) -> int | None:
    try:
        datos = jwt.decode(token, _clave(), algorithms=[ALGORITMO])
        return int(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema),
    db: Session = Depends(get_db),
) -> Usuario:
    no_autorizado = HTTPException(
        status_code=401,
        detail="Sesión no válida o expirada. Inicia sesión de nuevo.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credenciales is None:
        raise no_autorizado
    usuario_id = decodificar_token(credenciales.credentials)
    usuario = db.get(Usuario, usuario_id) if usuario_id is not None else None
    if usuario is None:
        raise no_autorizado
    return usuario


def requiere_docente(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    if usuario.rol != "docente":
        raise HTTPException(status_code=403, detail="Esta acción es solo para docentes.")
    return usuario


def requiere_rol(*roles: str):
    """Fábrica de dependencias: exige que el usuario tenga uno de los roles indicados (403 si no)."""

    def _dependencia(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción.")
        return usuario

    return _dependencia


requiere_admin = requiere_rol("admin")
requiere_coordinacion = requiere_rol("coordinador", "admin")
requiere_seguimiento = requiere_rol("docente", "coordinador", "admin")
