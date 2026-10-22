"""Orquestación de proveedores de IA con respaldo (fallback) automático."""
import logging
import time
from collections.abc import Callable
from typing import TypeVar

import httpx

from app.config import settings
from app.schemas import ResultadoIA
from pydantic import BaseModel

from app.services.ia.base import ProveedorIA
from app.services.ia.gemini import ProveedorGemini
from app.services.ia.groq_llm import ProveedorGroq
from app.services.ia.ollama import ProveedorOllama

log = logging.getLogger(__name__)

MAX_CARACTERES = 400_000

PROVEEDORES: dict[str, type[ProveedorIA]] = {
    "gemini": ProveedorGemini,
    "groq": ProveedorGroq,
    "ollama": ProveedorOllama,
}

MSG_SIN_PROVEEDORES = (
    "No hay proveedores de IA configurados. Agrega GEMINI_API_KEY o GROQ_API_KEY en backend/.env."
)


ESPERAS_REINTENTO = (2, 5)  # segundos de espera antes del 1.er y 2.o reintento


def _es_transitorio(e: Exception) -> bool:
    """True si el error parece de red o temporal (conexión, timeout, 429, 5xx)."""
    if isinstance(e, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError, ConnectionError, TimeoutError)):
        return True
    if isinstance(e, httpx.HTTPStatusError):
        codigo = e.response.status_code
    else:
        codigo = getattr(e, "status_code", None) or getattr(e, "code", None)
    if isinstance(codigo, int) and (codigo == 429 or 500 <= codigo < 600):
        return True
    nombre = type(e).__name__.lower()
    return "timeout" in nombre or "connection" in nombre


R = TypeVar("R")
BM = TypeVar("BM", bound=BaseModel)


def _con_reintentos(nombre: str, operacion: Callable[[], R]) -> R:
    """Reintenta (2 s y 5 s) solo ante errores transitorios; otros errores se propagan."""
    intento = 0
    while True:
        try:
            return operacion()
        except Exception as e:
            if nombre == "ollama" or intento >= len(ESPERAS_REINTENTO) or not _es_transitorio(e):
                raise
            espera = ESPERAS_REINTENTO[intento]
            intento += 1
            log.warning("Error transitorio en %s (%s); reintento %d en %d s", nombre, type(e).__name__, intento, espera)
            time.sleep(espera)


def _generar_con_reintentos(proveedor: ProveedorIA, nombre: str, texto: str, num_preguntas: int) -> ResultadoIA:
    return _con_reintentos(nombre, lambda: proveedor.generar(texto, num_preguntas))


def proveedores_configurados() -> dict[str, bool]:
    """Estado (configurado o no) de cada proveedor conocido."""
    return {n: c().configurado() for n, c in PROVEEDORES.items()}


def _recorrer_proveedores(operacion: Callable[[ProveedorIA, str], R]) -> tuple[R, str]:
    """Prueba los proveedores en el orden de settings.lista_proveedores.

    Salta los que no tienen clave, captura errores y pasa al siguiente.
    Ollama (local, sin clave) solo se intenta si está en la lista y su URL
    responde; si no está levantado, falla rápido y se registra.
    """
    fallos: list[str] = []
    for nombre in settings.lista_proveedores:
        clase = PROVEEDORES.get(nombre)
        if clase is None:
            log.warning("Proveedor desconocido: %s", nombre)
            continue
        proveedor = clase()
        if not proveedor.configurado():
            log.info("Proveedor %s sin clave; se omite", nombre)
            continue
        try:
            return _con_reintentos(nombre, lambda: operacion(proveedor, nombre)), nombre
        except httpx.ConnectError:
            log.info("Proveedor %s no disponible (sin conexión); se omite", nombre)
        except Exception as e:
            log.exception("Falló el proveedor %s", nombre)
            fallos.append(f"{nombre}: {type(e).__name__}: {str(e)[:150]}")
    if not fallos:
        raise RuntimeError(MSG_SIN_PROVEEDORES)
    raise RuntimeError("Todos los proveedores de IA fallaron. " + " | ".join(fallos))


def generar_con_respaldo(texto: str, num_preguntas: int) -> tuple[ResultadoIA, str]:
    """Genera resumen y cuestionario con el primer proveedor que responda."""
    if len(texto) > MAX_CARACTERES:
        log.warning("Transcripción de %d caracteres truncada a %d", len(texto), MAX_CARACTERES)
        texto = texto[:MAX_CARACTERES]
    return _recorrer_proveedores(lambda p, _n: p.generar(texto, num_preguntas))


def ejecutar_con_respaldo(prompt: str, esquema: type[BM]) -> tuple[BM, str]:
    """Tarea genérica de IA (tutor, calificación, verificación…): devuelve (objeto validado, proveedor)."""
    return _recorrer_proveedores(lambda p, _n: p.completar_json(prompt, esquema))
