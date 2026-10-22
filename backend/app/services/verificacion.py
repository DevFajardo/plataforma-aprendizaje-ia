"""Verificación de calidad de las preguntas generadas: ¿están respaldadas por el video? ¿la respuesta es inequívoca?

Se hace una sola llamada de IA por cuestionario (en lote). Si la IA no está disponible, las preguntas quedan «sin
verificar» (verificacion = NULL) y el cuestionario se puede usar con normalidad.
"""
import json
import logging
import re
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import Transcripcion
from app.services import ia

log = logging.getLogger(__name__)

MAX_TRANSCRIPCION = 300_000


class VerificacionPregunta(BaseModel):
    numero: int = Field(description="Número de la pregunta (el mismo de la lista, desde 1)")
    respaldo: Literal["si", "parcial", "no"] = Field(description="¿La pregunta y su respuesta están respaldadas por la transcripción?")
    cita: str = Field(default="", description="Fragmento textual breve de la transcripción que lo respalda (vacío si no hay)")
    marca_tiempo: str = Field(default="", description="Marca mm:ss de la cita")
    respuesta_inequivoca: bool = Field(description="¿La respuesta correcta es la única defendible entre las opciones?")
    problemas: list[str] = Field(default_factory=list, description="Problemas de redacción o de diseño, en español")


class LoteVerificacion(BaseModel):
    preguntas: list[VerificacionPregunta]


def construir_prompt(transcripcion_texto: str, preguntas: list) -> str:
    bloques = []
    for i, p in enumerate(preguntas, 1):
        opciones = json.loads(p.opciones_json or "[]")
        ops = "\n".join(f"   {chr(65 + k)}) {o}" for k, o in enumerate(opciones))
        bloques.append(f"{i}. [{p.tipo}] {p.enunciado}\n{ops}\n   Respuesta marcada como correcta: {p.respuesta_correcta}")
    return f"""Eres un revisor de calidad de evaluaciones. Revisa cada pregunta de un cuestionario generado a partir de un video.

Para CADA pregunta determina:
1. "respaldo": "si" si la pregunta y su respuesta correcta están claramente respaldadas por la transcripción; "parcial" si solo lo están en parte o requieren suponer algo; "no" si no aparecen en la transcripción o la contradicen.
2. "cita": un fragmento textual breve de la transcripción que lo respalda (vacío si respaldo es "no") y su "marca_tiempo" mm:ss.
3. "respuesta_inequivoca": true solo si la respuesta marcada es la ÚNICA defendible; false si otra opción también podría ser correcta, si hay dos correctas o si la marcada es dudosa. En preguntas abiertas indica si el criterio de la respuesta modelo es claro.
4. "problemas": lista de problemas de redacción o diseño (ambigüedad, pistas en el enunciado, opciones absurdas o repetidas, negaciones confusas…). Lista vacía si no hay.

Responde en español, con una entrada por pregunta usando su número, sin omitir ninguna.

PREGUNTAS:
{chr(10).join(bloques)}

TRANSCRIPCIÓN (con marcas [mm:ss]):
{transcripcion_texto}
"""


def _estado(v: VerificacionPregunta) -> str:
    return "verificada" if v.respaldo == "si" and v.respuesta_inequivoca and not v.problemas else "revisar"


def _marca_valida(marca: str) -> str:
    return marca.strip() if re.fullmatch(r"(\d{1,2}:)?\d{1,3}:\d{2}", marca.strip()) else ""


def verificar_preguntas(transcripcion: Transcripcion, preguntas: list) -> bool:
    """Verifica en lote y guarda `Pregunta.verificacion` (JSON). Devuelve False si la IA falla (no lanza)."""
    if not preguntas:
        return True
    try:
        texto = transcripcion.texto_con_tiempos()[:MAX_TRANSCRIPCION]
        lote, proveedor = ia.ejecutar_con_respaldo(construir_prompt(texto, preguntas), LoteVerificacion)
        por_numero = {v.numero: v for v in lote.preguntas}
        resultados = {}
        for i, p in enumerate(preguntas, 1):
            v = por_numero.get(i)
            if v is None:
                continue
            resultados[p] = json.dumps(
                {
                    "estado": _estado(v),
                    "respaldo": v.respaldo,
                    "cita": v.cita.strip()[:400],
                    "marca_tiempo": _marca_valida(v.marca_tiempo),
                    "inequivoca": v.respuesta_inequivoca,
                    "problemas": [x.strip() for x in v.problemas if x.strip()][:5],
                    "proveedor": proveedor,
                },
                ensure_ascii=False,
            )
    except Exception:
        log.exception("No se pudo verificar la calidad de las preguntas; quedan sin verificar")
        return False
    for p, texto_json in resultados.items():
        p.verificacion = texto_json
    return True
