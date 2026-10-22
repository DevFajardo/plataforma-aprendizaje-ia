"""Adaptador de Google Gemini (SDK google-genai) con salida estructurada."""
from google import genai

from app.config import settings
from app.schemas import ResultadoIA
from app.services.ia.base import ProveedorIA, T, construir_prompt


class ProveedorGemini(ProveedorIA):
    nombre = "gemini"

    def configurado(self) -> bool:
        return bool(settings.gemini_api_key)

    def generar(self, transcripcion_texto: str, num_preguntas: int) -> ResultadoIA:
        cliente = genai.Client(api_key=settings.gemini_api_key)
        resp = cliente.models.generate_content(
            model=settings.gemini_model,
            contents=construir_prompt(transcripcion_texto, num_preguntas),
            config={"response_mime_type": "application/json", "response_schema": ResultadoIA},
        )
        if isinstance(resp.parsed, ResultadoIA):
            return resp.parsed
        return ResultadoIA.model_validate_json(resp.text)

    def completar_json(self, prompt: str, esquema: type[T]) -> T:
        cliente = genai.Client(api_key=settings.gemini_api_key)
        resp = cliente.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={"response_mime_type": "application/json", "response_schema": esquema},
        )
        if isinstance(resp.parsed, esquema):
            return resp.parsed
        return esquema.model_validate_json(resp.text)
