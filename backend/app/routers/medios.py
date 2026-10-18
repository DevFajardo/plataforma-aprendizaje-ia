"""Servicio de archivos de video/audio subidos (con soporte de Range para saltar en el reproductor)."""
import mimetypes
import re

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse

from app.routers import procesar
from app.routers.procesar import EXTENSIONES_PERMITIDAS

router = APIRouter(prefix="/api", tags=["medios"])

# Nombres generados por el servidor: uuid hex + extensión permitida (no adivinables, sin rutas)
_PATRON = re.compile(r"^[0-9a-f]{32}\.([a-z0-9]{2,4})$")


@router.get("/medios/{nombre}")
def obtener_medio(nombre: str):
    m = _PATRON.fullmatch(nombre)
    if not m or m.group(1) not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(status_code=400, detail="Nombre de archivo no válido.")
    ruta = procesar.CARPETA_SUBIDAS / nombre
    if not ruta.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    tipo = mimetypes.guess_type(nombre)[0] or "application/octet-stream"
    return FileResponse(ruta, media_type=tipo)  # Starlette atiende cabeceras Range (206)
