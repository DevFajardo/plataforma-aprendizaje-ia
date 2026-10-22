"""Esquemas de la estructura académica, los cursos, el panel de coordinación y las alertas (Sprint 6)."""
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas_api import FechaUTC

PATRON_PERIODO = re.compile(r"^\d{4}-\d{1,2}$")


# ---------- Administración de la estructura ----------

class FacultadIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)


class FacultadOut(BaseModel):
    id: int
    nombre: str
    num_programas: int = 0


class ProgramaIn(BaseModel):
    facultad_id: int
    nombre: str = Field(min_length=2, max_length=150)
    codigo: str = Field(min_length=1, max_length=20)


class ProgramaEditarIn(BaseModel):
    facultad_id: int | None = None
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    codigo: str | None = Field(default=None, min_length=1, max_length=20)


class ProgramaOut(BaseModel):
    id: int
    facultad_id: int
    facultad: str
    nombre: str
    codigo: str


class AsignaturaIn(BaseModel):
    programa_id: int
    nombre: str = Field(min_length=2, max_length=150)
    codigo: str = Field(min_length=1, max_length=20)
    semestre: int = Field(default=1, ge=1, le=12)


class AsignaturaEditarIn(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    codigo: str | None = Field(default=None, min_length=1, max_length=20)
    semestre: int | None = Field(default=None, ge=1, le=12)


class AsignaturaOut(BaseModel):
    id: int
    programa_id: int
    programa: str
    nombre: str
    codigo: str
    semestre: int
    ra_ids: list[int] = []


class AsignaturaRasIn(BaseModel):
    ra_ids: list[int]


class RaIn(BaseModel):
    programa_id: int
    codigo: str = Field(min_length=1, max_length=20)
    descripcion: str = Field(min_length=3, max_length=2000)


class RaEditarIn(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=20)
    descripcion: str | None = Field(default=None, min_length=3, max_length=2000)


class RaOut(BaseModel):
    id: int
    programa_id: int
    programa: str
    codigo: str
    descripcion: str


class UsuarioAdminOut(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    programa_id: int | None = None
    programa: str | None = None


class UsuarioAdminIn(BaseModel):
    rol: Literal["estudiante", "docente", "coordinador", "admin"] | None = None
    programa_id: int | None = None  # null explícito = quitar el programa


# ---------- Cursos ----------

class GrupoIn(BaseModel):
    asignatura_id: int
    periodo: str
    nombre: str = Field(min_length=1, max_length=100)

    @field_validator("periodo")
    @classmethod
    def _periodo(cls, v: str):
        v = v.strip()
        if not PATRON_PERIODO.match(v):
            raise ValueError('El periodo debe tener el formato "2026-2".')
        return v


class GrupoEditarIn(BaseModel):
    periodo: str | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("periodo")
    @classmethod
    def _periodo(cls, v: str | None):
        if v is None:
            return v
        v = v.strip()
        if not PATRON_PERIODO.match(v):
            raise ValueError('El periodo debe tener el formato "2026-2".')
        return v


class GrupoOut(BaseModel):
    id: int
    nombre: str
    periodo: str
    codigo_ingreso: str
    asignatura_id: int
    asignatura: str
    programa: str
    docente: str
    num_matriculados: int
    num_cuestionarios: int


class MatriculadoOut(BaseModel):
    estudiante_id: int
    nombre: str
    email: str
    desde: FechaUTC


class UnirseGrupoIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=10)


class CuestionarioCursoOut(BaseModel):
    id: int
    titulo: str
    num_preguntas: int
    mejor_puntaje: int | None = None
    mejor_total: int | None = None


class MiCursoOut(BaseModel):
    grupo_id: int
    nombre: str
    periodo: str
    asignatura: str
    programa: str
    docente: str
    cuestionarios: list[CuestionarioCursoOut]


# ---------- Panel de coordinación ----------

Semaforo = Literal["verde", "amarillo", "rojo", "sin_datos"]


class LogroRa(BaseModel):
    ra_id: int
    codigo: str
    descripcion: str
    programa: str
    logro: float | None
    respuestas: int
    estudiantes: int
    semaforo: Semaforo


class LogroBloom(BaseModel):
    nivel: str
    preguntas: int
    respuestas: int
    logro: float | None


class LogroGrupo(BaseModel):
    grupo_id: int
    nombre: str
    periodo: str
    docente: str
    logro: float | None
    respuestas: int
    estudiantes: int
    semaforo: Semaforo


class LogroAsignatura(BaseModel):
    asignatura_id: int
    nombre: str
    codigo: str
    logro: float | None
    respuestas: int
    estudiantes: int
    semaforo: Semaforo
    grupos: list[LogroGrupo]


class PuntoTendencia(BaseModel):
    semana: str  # lunes de la semana, AAAA-MM-DD
    logro: float
    respuestas: int


class ProgramaBasico(BaseModel):
    id: int
    nombre: str


class CoordinacionOut(BaseModel):
    programas: list[ProgramaBasico]  # programas que el usuario puede consultar
    programa_id: int | None  # None = todos (solo admin)
    programa_nombre: str
    periodo: str | None
    periodos: list[str]
    logro_global: float | None
    respuestas: int
    estudiantes: int
    ras: list[LogroRa]
    bloom: list[LogroBloom]
    asignaturas: list[LogroAsignatura]
    tendencia: list[PuntoTendencia]


# ---------- Alertas tempranas ----------

class MotivoAlerta(BaseModel):
    codigo: Literal["inactividad", "bajo_promedio", "repasos_vencidos", "caida"]
    texto: str


class AlertaOut(BaseModel):
    grupo_id: int
    grupo: str
    asignatura: str
    estudiante_id: int
    nombre: str
    email: str
    nivel: Literal["alto", "medio"]
    motivos: list[MotivoAlerta]


class AtenderAlertaIn(BaseModel):
    grupo_id: int
    estudiante_id: int
    nota: str = Field(default="", max_length=1000)


class SeguimientoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    grupo_id: int
    estudiante_id: int
    motivos: str
    nota: str
    creado_en: FechaUTC
