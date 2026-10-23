"""Esquemas de entrada/salida de la API (separados de los que usa el adaptador de IA)."""
import json
import re
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator, model_serializer, model_validator


def _a_utc(v: datetime) -> datetime:
    """SQLite devuelve datetimes sin zona; en la BD siempre son UTC, así que se marcan como tal.

    Con zona, Pydantic los serializa como ISO 8601 con "Z" y el navegador los muestra en hora local.
    """
    return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)


FechaUTC = Annotated[datetime, AfterValidator(_a_utc)]


# ---------- Autenticación ----------

class RegistroIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    rol: Literal["estudiante", "docente"] = "estudiante"
    # Ley 1581 de 2012: la aceptación de la política de datos es obligatoria; la de investigación, opcional
    acepta_tratamiento_datos: bool = False
    consentimiento_investigacion: bool = False

    @model_validator(mode="after")
    def _exigir_politica(self):
        if not self.acepta_tratamiento_datos:
            raise ValueError("Debes aceptar la política de tratamiento de datos personales para registrarte.")
        return self


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    email: str
    rol: str
    programa_id: int | None = None
    acepta_tratamiento_datos: bool = False
    consentimiento_investigacion: bool = False
    tutorial_visto: list[str] = []

    @field_validator("tutorial_visto", mode="before")
    @classmethod
    def _leer_tutorial(cls, v):
        """En la BD es un texto JSON; en la API, una lista de roles."""
        if v is None:
            return []
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except ValueError:
                return []
        return [str(x) for x in v] if isinstance(v, list) else []


class TutorialIn(BaseModel):
    visto: bool


class CuentaEditarIn(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    password_actual: str | None = Field(default=None, max_length=128)
    password_nueva: str | None = Field(default=None, min_length=8, max_length=128)
    consentimiento_investigacion: bool | None = None
    acepta_tratamiento_datos: bool | None = None  # permite aceptar la política a cuentas anteriores a la Ley 1581


class EliminarCuentaIn(BaseModel):
    password: str = Field(max_length=128)


class TokenOut(BaseModel):
    token: str
    usuario: UsuarioOut


# ---------- Procesamiento ----------

class ProcesarIn(BaseModel):
    url: HttpUrl
    num_preguntas: int = Field(default=8, ge=3, le=20)


class TareaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    url: str
    estado: str
    mensaje: str
    fuente_transcripcion: str | None = None
    proveedor_ia: str | None = None
    cuestionario_id: int | None = None


# ---------- Sprint 8: modelos compartidos ----------

# ---------- Verificación de calidad ----------

class VerificacionOut(BaseModel):
    estado: Literal["verificada", "revisar"]
    respaldo: Literal["si", "parcial", "no"]
    cita: str = ""
    marca_tiempo: str = ""
    inequivoca: bool = True
    problemas: list[str] = []


# ---------- Calificación de abiertas ----------

class CalificacionIAOut(BaseModel):
    puntaje: int
    nivel: Literal["insuficiente", "basico", "bueno", "excelente"]
    retroalimentacion: str
    falto: str = ""


# ---------- Psicometría ----------

class DistractorOut(BaseModel):
    opcion: str
    letra: str
    correcta: bool
    porcentaje: float
    porcentaje_superior: float | None = None
    porcentaje_inferior: float | None = None
    funcional: bool | None = None
    confunde_mejores: bool = False


class ItemAnalisisOut(BaseModel):
    pregunta_id: int
    orden: int
    enunciado: str
    n: int
    suficiente: bool
    p: float | None = None
    d: float | None = None
    r_pb: float | None = None
    dificultad: str = ""
    discriminacion: str = ""
    distractores: list[DistractorOut] = []
    observaciones: list[str] = []
    revisar: bool = False



# ---------- Cuestionarios ----------

class PreguntaOut(BaseModel):
    id: int
    orden: int
    tipo: str
    enunciado: str
    opciones: list[str]
    marca_tiempo: str
    # Solo se rellenan para el creador
    respuesta_correcta: str | None = None
    explicacion: str | None = None
    ra_id: int | None = None
    nivel_bloom: str | None = None
    verificacion: VerificacionOut | None = None  # solo el creador; None = sin verificar
    banco_id: int | None = None  # solo el creador


class RepasoEstado(BaseModel):
    disponible_desde: FechaUTC
    vencido: bool


class CuestionarioDetalle(BaseModel):
    id: int
    video_id: int
    titulo: str
    resumen: str
    ideas_clave: list[str]
    proveedor_ia: str
    num_preguntas: int
    publicado: bool
    codigo_compartir: str | None = None  # solo el creador
    es_creador: bool
    youtube_id: str | None
    medio: Literal["youtube", "vimeo", "video", "audio"] = "youtube"
    video_externo_id: str | None = None  # id en YouTube/Vimeo
    vimeo_hash: str | None = None  # videos no listados de Vimeo
    archivo_url: str | None = None  # ruta relativa /api/medios/{nombre} cuando el video es un archivo
    url: str
    creado_en: FechaUTC
    modo: Literal["aprendizaje", "control"] = "aprendizaje"
    repaso_dias: int | None = None
    repaso: RepasoEstado | None = None  # repaso pendiente del usuario en este cuestionario
    # Solo el creador
    segundos_edicion: int | None = None
    estimacion_manual_min: int | None = None
    publicado_en: FechaUTC | None = None
    grupo_id: int | None = None
    grupo_nombre: str | None = None
    asignatura_nombre: str | None = None
    preguntas: list[PreguntaOut]


class CuestionarioResumen(BaseModel):
    id: int
    titulo: str
    creado_en: FechaUTC
    num_preguntas: int
    youtube_id: str | None
    plataforma: str = "youtube"
    modo: str = "aprendizaje"
    publicado: bool
    mejor_puntaje: int | None = None
    mejor_total: int | None = None
    propio: bool = True  # False = cuestionario ajeno al que me uní
    creador: str | None = None


# ---------- Intentos ----------

class IntentoCreado(BaseModel):
    id: int
    cuestionario_id: int
    tipo: Literal["inicial", "practica", "diferido"] = "inicial"
    con_feedback: bool = True  # False en repasos diferidos y en el modo grupo control


class RespuestaIn(BaseModel):
    pregunta_id: int
    respuesta: str = Field(max_length=5000)


class RespuestaOut(BaseModel):
    registrada: bool = True
    con_feedback: bool = True
    # Sin retroalimentación (repaso diferido / grupo control) solo se devuelve `registrada`
    correcta: bool | None = None
    respuesta_correcta: str = ""
    explicacion: str = ""
    marca_tiempo: str = ""
    # Preguntas abiertas: calificación sugerida por la IA (no aparece en control ni en diferido, ni si la IA falla)
    calificacion_ia: CalificacionIAOut | None = None

    @model_serializer(mode="wrap")
    def _omitir_calificacion_vacia(self, handler):
        """Sin calificación de la IA la clave no se envía (la respuesta queda igual que antes del Sprint 8)."""
        datos = handler(self)
        if datos.get("calificacion_ia") is None:
            datos.pop("calificacion_ia", None)
        return datos


class RevisionPregunta(BaseModel):
    pregunta_id: int
    enunciado: str
    respuesta: str
    correcta: bool | None
    respuesta_correcta: str
    explicacion: str
    marca_tiempo: str


class IntentoResumen(BaseModel):
    id: int
    cuestionario_id: int
    puntaje: int
    total: int
    porcentaje: float
    finalizado: bool
    creado_en: FechaUTC
    tipo: Literal["inicial", "practica", "diferido"] = "inicial"
    # Respuestas correctas al terminar un repaso diferido (nunca en el grupo control)
    revision: list[RevisionPregunta] | None = None
    repaso_disponible_desde: FechaUTC | None = None  # tras el intento inicial, cuándo toca el repaso


class IntentoHistorial(IntentoResumen):
    cuestionario_titulo: str


class RepasoOut(BaseModel):
    id: int
    cuestionario_id: int
    cuestionario_titulo: str
    disponible_desde: FechaUTC
    vencido: bool


# ---------- Publicar y compartir ----------

class PublicarIn(BaseModel):
    publicado: bool
    grupo_id: int | None = None  # opcional: asigna el cuestionario a uno de los grupos del docente al publicar
    estimacion_manual_min: int | None = Field(default=None, ge=1, le=100000)


class DuplicarIn(BaseModel):
    modo: Literal["aprendizaje", "control"] = "control"
    titulo: str | None = Field(default=None, min_length=1, max_length=300)


class TiempoEdicionIn(BaseModel):
    segundos: int = Field(ge=1, le=4 * 3600)  # máximo 4 h por llamada


class CompartidoOut(BaseModel):
    cuestionario_id: int
    titulo: str
    creador: str


# ---------- Edición por el docente ----------

class CuestionarioEditarIn(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=300)
    resumen: str | None = Field(default=None, min_length=1, max_length=20000)
    ideas_clave: list[str] | None = Field(default=None, max_length=30)
    # Admiten null explícito (quitar el repaso / la estimación): se distingue con model_fields_set
    repaso_dias: int | None = None
    estimacion_manual_min: int | None = Field(default=None, ge=1, le=100000)
    grupo_id: int | None = None  # null explícito = quitar del grupo

    @field_validator("repaso_dias")
    @classmethod
    def _repaso_permitido(cls, v: int | None):
        if v is not None and v not in (1, 3, 7, 14):
            raise ValueError("El repaso diferido debe ser a 1, 3, 7 o 14 días.")
        return v

    @field_validator("ideas_clave")
    @classmethod
    def _limpiar_ideas(cls, v: list[str] | None):
        if v is None:
            return v
        return [i.strip() for i in v if i.strip()]


class PreguntaIn(BaseModel):
    tipo: Literal["opcion_multiple", "verdadero_falso", "abierta"]
    enunciado: str = Field(min_length=1, max_length=2000)
    opciones: list[str] = Field(default_factory=list)
    respuesta_correcta: str = Field(min_length=1, max_length=5000)
    explicacion: str = Field(default="", max_length=5000)
    marca_tiempo: str = Field(default="", max_length=20)
    ra_id: int | None = None
    nivel_bloom: Literal["recordar", "comprender", "aplicar", "analizar", "evaluar", "crear"] | None = None

    @model_validator(mode="after")
    def _validar(self):
        self.enunciado = self.enunciado.strip()
        self.respuesta_correcta = self.respuesta_correcta.strip()
        if not self.enunciado or not self.respuesta_correcta:
            raise ValueError("El enunciado y la respuesta correcta no pueden estar vacíos.")
        self.marca_tiempo = self.marca_tiempo.strip()
        if self.marca_tiempo and not re.fullmatch(r"(\d{1,2}:)?\d{1,2}:\d{2}", self.marca_tiempo):
            raise ValueError("La marca de tiempo debe tener el formato mm:ss.")
        if self.tipo == "opcion_multiple":
            ops = [o.strip() for o in self.opciones]
            if not 2 <= len(ops) <= 6:
                raise ValueError("Una pregunta de opción múltiple necesita entre 2 y 6 opciones.")
            if any(not o for o in ops) or len(set(ops)) != len(ops):
                raise ValueError("Las opciones no pueden estar vacías ni repetidas.")
            if self.respuesta_correcta not in ops:
                raise ValueError("La respuesta correcta debe ser una de las opciones.")
            self.opciones = ops
        elif self.tipo == "verdadero_falso":
            if self.opciones and self.opciones != ["Verdadero", "Falso"]:
                raise ValueError('En verdadero/falso las opciones deben ser ["Verdadero", "Falso"].')
            self.opciones = ["Verdadero", "Falso"]
            if self.respuesta_correcta not in self.opciones:
                raise ValueError('La respuesta correcta debe ser "Verdadero" o "Falso".')
        else:
            self.opciones = []
        return self


class ReordenarIn(BaseModel):
    ids: list[int]


# ---------- Resultados para el docente ----------

class IntentoResultado(BaseModel):
    intento_id: int
    nombre: str
    email: str
    puntaje: int
    total: int
    porcentaje: float
    fecha: FechaUTC
    tipo: str = "inicial"
    consentimiento_investigacion: bool = False


class RespuestaAbiertaOut(BaseModel):
    intento_id: int | None = None
    nombre: str
    respuesta: str
    sugerida: CalificacionIAOut | None = None  # nota sugerida por la IA
    nota_final: int | None = None  # nota aprobada/ajustada por el docente; None = pendiente


class PreguntaResultado(BaseModel):
    pregunta_id: int
    orden: int
    tipo: str
    enunciado: str
    num_respuestas: int
    porcentaje_acierto: float | None = None  # None en preguntas abiertas
    ra_codigo: str | None = None
    nivel_bloom: str | None = None
    respuestas_abiertas: list[RespuestaAbiertaOut] = []


class EstudianteGanancia(BaseModel):
    nombre: str
    email: str
    intentos: int
    primer_porcentaje: float
    ultimo_porcentaje: float
    diferencia: float  # puntos porcentuales (último - primero)


class GananciaAprendizaje(BaseModel):
    """Medida pre-test/post-test: primer intento vs. último intento de quienes repitieron el cuestionario."""

    estudiantes: int  # estudiantes con al menos 2 intentos finalizados
    promedio_primer_intento: float | None = None
    promedio_ultimo_intento: float | None = None
    diferencia_puntos: float | None = None
    detalle: list[EstudianteGanancia] = []


class EstudianteRetencion(BaseModel):
    nombre: str
    email: str
    inicial: float  # % del intento inicial
    diferido: float  # % del intento diferido
    retencion: float | None  # diferido / inicial x 100 (None si el inicial fue 0 %)
    diferencia: float  # diferido - inicial (puntos porcentuales)


class RetencionOut(BaseModel):
    """Post-test diferido: intento inicial vs. intento diferido de los estudiantes que hicieron ambos."""

    repaso_dias: int | None = None
    estudiantes: int
    promedio_inicial: float | None = None
    promedio_diferido: float | None = None
    retencion_pct: float | None = None  # promedio diferido / promedio inicial x 100
    diferencia_puntos: float | None = None
    detalle: list[EstudianteRetencion] = []


class ResultadosOut(BaseModel):
    titulo: str
    modo: str = "aprendizaje"
    total_intentos: int
    estudiantes_unicos: int
    promedio_porcentaje: float
    intentos: list[IntentoResultado]
    preguntas: list[PreguntaResultado]
    ganancia: GananciaAprendizaje
    retencion: RetencionOut
    # Análisis de ítems (intentos iniciales finalizados); se exige un mínimo de respuestas por pregunta
    items: list[ItemAnalisisOut] = []
    items_minimo: int = 5
    items_intentos: int = 0


# ---------- Comparación de grupos (cuasi-experimento) ----------

class MetricaGrupo(BaseModel):
    n: int
    media: float | None = None
    desviacion: float | None = None  # desviación estándar muestral (n - 1); None si n < 2


class Efecto(BaseModel):
    diferencia_medias: float | None = None  # media de A - media de B
    d_cohen: float | None = None
    interpretacion: str


class GrupoComparacion(BaseModel):
    id: int
    titulo: str
    modo: str
    inicial: MetricaGrupo
    diferido: MetricaGrupo
    retencion: MetricaGrupo


class ComparacionOut(BaseModel):
    a: GrupoComparacion
    b: GrupoComparacion
    efecto_inicial: Efecto
    efecto_diferido: Efecto
    efecto_retencion: Efecto
    nota: str


# ---------- Estadísticas ----------

class PuntoEvolucion(BaseModel):
    fecha: FechaUTC
    porcentaje: float
    cuestionario_titulo: str


class TemaReforzar(BaseModel):
    pregunta_id: int
    enunciado: str
    cuestionario_id: int
    cuestionario_titulo: str
    fallos: int


class ResumenCuestionarioDocente(BaseModel):
    id: int
    titulo: str
    intentos: int
    promedio: float | None = None
    codigo_compartir: str


class TiempoDocente(BaseModel):
    """Tiempo con la herramienta (generación + edición) frente a la estimación del tiempo manual."""

    cuestionarios_con_estimacion: int
    promedio_herramienta_min: float | None = None
    promedio_manual_min: float | None = None
    ahorro_pct: float | None = None  # (manual - herramienta) / manual x 100


class EstadisticasDocente(BaseModel):
    cuestionarios_publicados: int
    estudiantes_unicos: int
    intentos_recibidos: int
    promedio_general: float | None = None
    por_cuestionario: list[ResumenCuestionarioDocente]
    tiempo: TiempoDocente


class EstadisticasOut(BaseModel):
    rol: str
    intentos_finalizados: int
    promedio_porcentaje: float | None = None
    mejor_porcentaje: float | None = None
    retencion_promedio: float | None = None  # promedio de (diferido / inicial x 100) de tus repasos completados
    cuestionarios_generados: int
    cuestionarios_unidos: int
    evolucion: list[PuntoEvolucion]
    temas_a_reforzar: list[TemaReforzar]
    docente: EstadisticasDocente | None = None


# ---------- Encuesta SUS ----------

class SusIn(BaseModel):
    respuestas: list[int] = Field(min_length=10, max_length=10)
    comentario: str | None = Field(default=None, max_length=2000)

    @field_validator("respuestas")
    @classmethod
    def _rango(cls, v: list[int]):
        if any(not 1 <= r <= 5 for r in v):
            raise ValueError("Cada respuesta debe estar entre 1 y 5.")
        return v

    @field_validator("comentario")
    @classmethod
    def _limpiar(cls, v: str | None):
        v = (v or "").strip()
        return v or None


class SusOut(BaseModel):
    respuestas: list[int]
    puntaje: float
    interpretacion: str
    comentario: str | None = None
    creado_en: FechaUTC


class SusResumen(BaseModel):
    n: int
    promedio: float | None = None
    desviacion: float | None = None
    minimo: float | None = None
    maximo: float | None = None
    interpretacion_promedio: str | None = None
    distribucion: dict[str, int]
    promedio_por_item: list[float]


# ---------- Notificaciones (Sprint 7) ----------

class NotificacionOut(BaseModel):
    id: int
    tipo: str
    titulo: str
    mensaje: str
    enlace: str
    leida: bool
    creada_en: FechaUTC


class NotificacionesPagina(BaseModel):
    items: list[NotificacionOut]
    total: int
    pagina: int
    por_pagina: int
    no_leidas: int


class ContadorNotificaciones(BaseModel):
    no_leidas: int
