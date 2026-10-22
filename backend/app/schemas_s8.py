"""Esquemas de la API del Sprint 8: tutor IA, calificación de abiertas, verificación, psicometría y banco."""
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas_api import FechaUTC, VerificacionOut


# ---------- Calificación de abiertas ----------

class NotaAbiertaIn(BaseModel):
    nota: int = Field(ge=0, le=100)


# ---------- Tutor ----------

class CitaOut(BaseModel):
    marca_tiempo: str
    fragmento: str


class MensajeTutorOut(BaseModel):
    id: int
    rol: Literal["usuario", "tutor"]
    texto: str
    citas: list[CitaOut] = []
    creado_en: FechaUTC


class TutorEstado(BaseModel):
    habilitado: bool
    motivo: str = ""  # por qué está deshabilitado
    conversacion_id: int | None = None
    mensajes: list[MensajeTutorOut] = []
    restantes: int
    limite: int
    sugerencias: list[str] = []


class PreguntaTutorIn(BaseModel):
    pregunta: str = Field(min_length=1, max_length=1000)


class RespuestaTutorOut(BaseModel):
    usuario: MensajeTutorOut
    tutor: MensajeTutorOut
    restantes: int


# ---------- Banco de preguntas ----------

class GuardarEnBancoIn(BaseModel):
    visibilidad: Literal["institucional", "privada"] = "institucional"
    etiquetas: list[str] = Field(default_factory=list, max_length=10)
    asignatura_nombre: str | None = Field(default=None, max_length=150)


class EditarBancoIn(BaseModel):
    visibilidad: Literal["institucional", "privada"] | None = None
    etiquetas: list[str] | None = Field(default=None, max_length=10)


class AgregarDesdeBancoIn(BaseModel):
    cuestionario_id: int


class EstadisticaBanco(BaseModel):
    respuestas: int
    porcentaje_acierto: float | None = None
    usos: int  # cuestionarios donde aparece


class PreguntaBancoOut(BaseModel):
    id: int
    autor: str
    es_mia: bool
    visibilidad: str
    tipo: str
    enunciado: str
    opciones: list[str]
    respuesta_correcta: str
    explicacion: str
    nivel_bloom: str | None
    ra_codigo: str | None
    ra_descripcion: str | None
    asignatura_nombre: str | None
    etiquetas: list[str]
    verificacion: VerificacionOut | None
    estado_verificacion: Literal["verificada", "revisar", "sin_verificar"]
    estadisticas: EstadisticaBanco | None = None
    creado_en: FechaUTC


class PaginaBanco(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    items: list[PreguntaBancoOut]


class FiltrosBanco(BaseModel):
    asignaturas: list[str]
    ras: list[str]
