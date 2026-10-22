"""Esquemas de la clase en vivo (Sprint 7)."""
from pydantic import BaseModel, Field

from app.schemas_api import FechaUTC


class IniciarVivoIn(BaseModel):
    segundos_por_pregunta: int = Field(default=30, ge=10, le=120)


class SesionVivoOut(BaseModel):
    id: int
    cuestionario_id: int
    titulo: str
    pin: str
    estado: str
    segundos_por_pregunta: int
    total_preguntas: int


class UnirseVivoIn(BaseModel):
    pin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    apodo: str = Field(min_length=1, max_length=40)


class UnidoVivoOut(BaseModel):
    pin: str
    apodo: str
    token: str


class RespuestaVivoIn(BaseModel):
    token: str = Field(min_length=10, max_length=64)
    respuesta: str = Field(min_length=1, max_length=2000)


class AccionVivoIn(BaseModel):
    accion: str = Field(pattern=r"^(iniciar|siguiente|saltar|finalizar)$")


class PreguntaHistorialVivo(BaseModel):
    pregunta_id: int
    orden: int
    enunciado: str
    tipo: str
    respuestas: int
    porcentaje_acierto: float | None = None


class SesionHistorialVivo(BaseModel):
    id: int
    creada_en: FechaUTC
    finalizada_en: FechaUTC | None = None
    estado: str
    pin: str
    participantes: int
    promedio_acierto: float | None = None  # % de aciertos sobre respuestas de preguntas cerradas
    preguntas: list[PreguntaHistorialVivo]
