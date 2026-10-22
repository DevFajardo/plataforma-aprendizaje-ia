"""Adaptador de Ollama (modelo local) mediante su API HTTP."""
import httpx

from app.config import settings
from app.schemas import ResultadoIA
from app.services.ia.base import ProveedorIA, T, construir_prompt


class ProveedorOllama(ProveedorIA):
    nombre = "ollama"

    def configurado(self) -> bool:
        # No requiere clave; se considera disponible si hay URL (se prueba al usarlo).
        return bool(settings.ollama_url)

    def generar(self, transcripcion_texto: str, num_preguntas: int) -> ResultadoIA:
        r = httpx.post(
            f"{settings.ollama_url.rstrip('/')}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [
                    {"role": "user", "content": construir_prompt(transcripcion_texto, num_preguntas)}
                ],
                "format": ResultadoIA.model_json_schema(),
                "stream": False,
            },
            timeout=httpx.Timeout(600.0, connect=5.0),
        )
        r.raise_for_status()
        return ResultadoIA.model_validate_json(r.json()["message"]["content"])

    def completar_json(self, prompt: str, esquema: type[T]) -> T:
        r = httpx.post(
            f"{settings.ollama_url.rstrip('/')}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [{"role": "user", "content": prompt}],
                "format": esquema.model_json_schema(),
                "stream": False,
            },
            timeout=httpx.Timeout(600.0, connect=5.0),
        )
        r.raise_for_status()
        return esquema.model_validate_json(r.json()["message"]["content"])
