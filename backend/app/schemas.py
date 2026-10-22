from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


# ---------- Resultado que genera la IA ----------

class Pregunta(BaseModel):
    tipo: Literal["opcion_multiple", "verdadero_falso", "abierta"]
    enunciado: str
    opciones: list[str] = Field(
        default_factory=list,
        description="4 opciones para opcion_multiple; ['Verdadero','Falso'] para verdadero_falso; vacío para abierta",
    )
    respuesta_correcta: str = Field(description="Texto exacto de la opción correcta, o respuesta modelo si es abierta")
    explicacion: str = Field(description="Por qué esa es la respuesta, basada en el video")
    marca_tiempo: str = Field(default="", description="Minuto aproximado del video, formato mm:ss")
    nivel_bloom: Literal["recordar", "comprender", "aplicar", "analizar", "evaluar", "crear"] | None = Field(
        default=None, description="Nivel de la taxonomía de Bloom (revisada) que evalúa la pregunta"
    )


class ResultadoIA(BaseModel):
    titulo: str
    resumen: str
    ideas_clave: list[str]
    preguntas: list[Pregunta]


# ---------- Transcripción ----------

class Segmento(BaseModel):
    inicio: float  # segundos
    texto: str


class Transcripcion(BaseModel):
    fuente: Literal["subtitulos_youtube", "whisper_groq"]
    idioma: str
    segmentos: list[Segmento]

    def texto_con_tiempos(self) -> str:
        lineas = []
        for s in self.segmentos:
            m, seg = divmod(int(s.inicio), 60)
            lineas.append(f"[{m:02d}:{seg:02d}] {s.texto}")
        return "\n".join(lineas)


# ---------- API ----------

class SolicitudProcesar(BaseModel):
    url: HttpUrl
    num_preguntas: int = Field(default=8, ge=3, le=20)


class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    transcribiendo = "transcribiendo"
    generando = "generando"
    listo = "listo"
    error = "error"


class Tarea(BaseModel):
    id: str
    url: str
    estado: EstadoTarea = EstadoTarea.pendiente
    mensaje: str = ""
    fuente_transcripcion: str | None = None
    proveedor_ia: str | None = None
    resultado: ResultadoIA | None = None
