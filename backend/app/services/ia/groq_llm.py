"""Adaptador de Groq (LLM Llama) con modo JSON."""
import json

from groq import Groq

from app.config import settings
from app.schemas import ResultadoIA
from app.services.ia.base import ProveedorIA, T, construir_prompt


class ProveedorGroq(ProveedorIA):
    nombre = "groq"

    def configurado(self) -> bool:
        return bool(settings.groq_api_key)

    def generar(self, transcripcion_texto: str, num_preguntas: int) -> ResultadoIA:
        esquema = json.dumps(ResultadoIA.model_json_schema(), ensure_ascii=False)
        prompt = (
            construir_prompt(transcripcion_texto, num_preguntas)
            + f"\nResponde SOLO con un objeto JSON que cumpla este JSON Schema:\n{esquema}"
        )
        cliente = Groq(api_key=settings.groq_api_key)
        resp = cliente.chat.completions.create(
            model=settings.groq_llm_model,
            messages=[
                {"role": "system", "content": "Respondes únicamente con JSON válido."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        return ResultadoIA.model_validate_json(resp.choices[0].message.content)

    def completar_json(self, prompt: str, esquema: type[T]) -> T:
        schema = json.dumps(esquema.model_json_schema(), ensure_ascii=False)
        cliente = Groq(api_key=settings.groq_api_key)
        resp = cliente.chat.completions.create(
            model=settings.groq_llm_model,
            messages=[
                {"role": "system", "content": "Respondes únicamente con JSON válido."},
                {"role": "user", "content": prompt + "\n\nResponde SOLO con un objeto JSON que cumpla este JSON Schema:\n" + schema},
            ],
            response_format={"type": "json_object"},
        )
        return esquema.model_validate_json(resp.choices[0].message.content)
