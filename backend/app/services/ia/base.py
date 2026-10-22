"""Contrato común de los proveedores de IA (patrón Strategy / Adapter).

Cada proveedor (Gemini, Groq, Ollama) es un *adaptador* que oculta su SDK y
expone la misma interfaz `ProveedorIA.generar`. El resto de la aplicación
trabaja contra esta abstracción (Strategy), por lo que se puede cambiar o
reordenar proveedores sin tocar la lógica de negocio.
"""
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from app.schemas import ResultadoIA

T = TypeVar("T", bound=BaseModel)


class ProveedorIA(ABC):
    """Estrategia abstracta: genera resumen y cuestionario desde una transcripción."""

    nombre: str = ""

    @abstractmethod
    def generar(self, transcripcion_texto: str, num_preguntas: int) -> ResultadoIA:
        """Devuelve el resumen y el cuestionario ya validados."""

    @abstractmethod
    def completar_json(self, prompt: str, esquema: type[T]) -> T:
        """Tarea genérica: responde al `prompt` con un objeto que cumple `esquema` (modelo Pydantic)."""

    @abstractmethod
    def configurado(self) -> bool:
        """True si el proveedor tiene lo necesario (clave API, etc.)."""


def construir_prompt(transcripcion_texto: str, num_preguntas: int) -> str:
    """Prompt compartido por todos los proveedores."""
    return f"""Eres un asistente educativo. A partir de la transcripción de un video, genera material de estudio.

REGLAS:
- Usa ÚNICAMENTE el contenido de la transcripción; no inventes datos externos.
- Responde siempre en español (título, resumen, ideas clave, preguntas, opciones y explicaciones), aunque la transcripción esté en otro idioma: en ese caso tradúcela mentalmente y escribe todo en español.
- Entrega: un título, un resumen claro (2 a 4 párrafos), una lista de ideas clave y exactamente {num_preguntas} preguntas.
- Mezcla los tipos de pregunta: "opcion_multiple" (4 opciones), "verdadero_falso" (opciones ["Verdadero","Falso"]) y "abierta" (opciones vacías; respuesta_correcta es una respuesta modelo).
- En preguntas de opción múltiple y verdadero/falso, "respuesta_correcta" debe coincidir EXACTAMENTE con el texto de una de las opciones.
- Cada pregunta debe incluir "explicacion" (por qué es correcta, según el video) y "marca_tiempo" en formato mm:ss, tomada de las marcas [mm:ss] de la transcripción donde se trata el tema.
- Clasifica cada pregunta en "nivel_bloom" según la taxonomía de Bloom revisada, usando exactamente uno de: "recordar", "comprender", "aplicar", "analizar", "evaluar", "crear".

TRANSCRIPCIÓN:
{transcripcion_texto}
"""
