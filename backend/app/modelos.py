"""Modelos SQLAlchemy 2.0."""
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Sin caracteres ambiguos (0/O, 1/I/L)
ALFABETO_CODIGO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def ahora() -> datetime:
    return datetime.now(timezone.utc)


def como_utc(valor: datetime) -> datetime:
    """SQLite devuelve datetimes sin zona; en la BD siempre son UTC."""
    return valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor.astimezone(timezone.utc)


def generar_codigo() -> str:
    return "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(6))


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20), default="estudiante")  # estudiante | docente | coordinador | admin
    # Sprint 6: el coordinador coordina un programa académico
    programa_id: Mapped[int | None] = mapped_column(ForeignKey("programas.id", ondelete="SET NULL"), nullable=True)
    # Ley 1581 de 2012: aceptación obligatoria de la política de datos y consentimiento opcional de investigación
    acepta_tratamiento_datos: Mapped[bool] = mapped_column(Boolean, default=False)
    consentimiento_investigacion: Mapped[bool] = mapped_column(Boolean, default=False)
    consentimiento_fecha: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    youtube_id: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)
    url: Mapped[str] = mapped_column(String(500))
    titulo_original: Mapped[str | None] = mapped_column(String(300), nullable=True)
    fuente_transcripcion: Mapped[str] = mapped_column(String(50))
    transcripcion_json: Mapped[str] = mapped_column(Text)
    archivo: Mapped[str | None] = mapped_column(String(100), nullable=True)  # nombre guardado en subidas/
    plataforma: Mapped[str] = mapped_column(String(20), default="youtube")  # youtube | vimeo | archivo
    video_externo_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)  # id en la plataforma
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Cuestionario(Base):
    __tablename__ = "cuestionarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    creador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(300))
    resumen: Mapped[str] = mapped_column(Text)
    ideas_clave_json: Mapped[str] = mapped_column(Text)
    proveedor_ia: Mapped[str] = mapped_column(String(50))
    num_preguntas: Mapped[int] = mapped_column(Integer)
    codigo_compartir: Mapped[str] = mapped_column(String(6), unique=True, index=True, default=generar_codigo)
    publicado: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    # Sprint 5
    modo: Mapped[str] = mapped_column(String(20), default="aprendizaje")  # aprendizaje | control
    repaso_dias: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1, 3, 7 o 14; nulo = sin repaso
    segundos_generacion: Mapped[int] = mapped_column(Integer, default=0)  # tarea: creada -> lista
    segundos_edicion: Mapped[int] = mapped_column(Integer, default=0)  # tiempo activo acumulado del docente
    publicado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimacion_manual_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Sprint 6: grupo (curso) al que se asigna el cuestionario
    grupo_id: Mapped[int | None] = mapped_column(ForeignKey("grupos.id", ondelete="SET NULL"), nullable=True, index=True)

    video: Mapped[Video] = relationship()
    grupo: Mapped["Grupo | None"] = relationship()
    preguntas: Mapped[list["Pregunta"]] = relationship(
        back_populates="cuestionario",
        order_by="Pregunta.orden",
        cascade="all, delete-orphan",
    )
    intentos: Mapped[list["Intento"]] = relationship(back_populates="cuestionario", cascade="all, delete-orphan")
    repasos: Mapped[list["Repaso"]] = relationship(cascade="all, delete-orphan")


class Pregunta(Base):
    __tablename__ = "preguntas"

    id: Mapped[int] = mapped_column(primary_key=True)
    cuestionario_id: Mapped[int] = mapped_column(ForeignKey("cuestionarios.id", ondelete="CASCADE"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    tipo: Mapped[str] = mapped_column(String(30))
    enunciado: Mapped[str] = mapped_column(Text)
    opciones_json: Mapped[str] = mapped_column(Text, default="[]")
    respuesta_correcta: Mapped[str] = mapped_column(Text)
    explicacion: Mapped[str] = mapped_column(Text, default="")
    marca_tiempo: Mapped[str] = mapped_column(String(20), default="")
    # Sprint 6: resultado de aprendizaje y nivel de la taxonomía de Bloom (opcionales)
    ra_id: Mapped[int | None] = mapped_column(
        ForeignKey("resultados_aprendizaje.id", ondelete="SET NULL"), nullable=True, index=True
    )
    nivel_bloom: Mapped[str | None] = mapped_column(String(15), nullable=True)
    # Sprint 8: verificación de calidad con IA (JSON; nulo = sin verificar) y vínculo con el banco institucional
    verificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    banco_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    cuestionario: Mapped[Cuestionario] = relationship(back_populates="preguntas")


class Tarea(Base):
    __tablename__ = "tareas"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    num_preguntas: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    mensaje: Mapped[str] = mapped_column(Text, default="")
    fuente_transcripcion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    proveedor_ia: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cuestionario_id: Mapped[int | None] = mapped_column(ForeignKey("cuestionarios.id", ondelete="SET NULL"), nullable=True)
    archivo: Mapped[str | None] = mapped_column(String(100), nullable=True)  # subida pendiente de procesar
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Intento(Base):
    __tablename__ = "intentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    cuestionario_id: Mapped[int] = mapped_column(ForeignKey("cuestionarios.id", ondelete="CASCADE"), index=True)
    puntaje: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    respuestas_json: Mapped[str] = mapped_column(Text, default="[]")  # [{pregunta_id, respuesta, correcta|null}]
    finalizado: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo: Mapped[str] = mapped_column(String(10), default="inicial")  # inicial | practica | diferido
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    cuestionario: Mapped[Cuestionario] = relationship(back_populates="intentos")


class Repaso(Base):
    """Post-test diferido: se crea al finalizar el intento inicial y vence `repaso_dias` días después."""

    __tablename__ = "repasos"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    cuestionario_id: Mapped[int] = mapped_column(ForeignKey("cuestionarios.id", ondelete="CASCADE"), index=True)
    disponible_desde: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completado_intento_id: Mapped[int | None] = mapped_column(
        ForeignKey("intentos.id", ondelete="SET NULL"), nullable=True
    )


class RespuestaSUS(Base):
    """Respuesta a la encuesta de usabilidad SUS (una por usuario; si responde de nuevo se actualiza)."""

    __tablename__ = "respuestas_sus"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True, index=True)
    respuestas_json: Mapped[str] = mapped_column(Text)  # lista de 10 enteros entre 1 y 5
    puntaje_sus: Mapped[float] = mapped_column(Float)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    usuario: Mapped[Usuario] = relationship()


# ---------- Sprint 6: estructura académica ----------

NIVELES_BLOOM = ("recordar", "comprender", "aplicar", "analizar", "evaluar", "crear")
ROLES = ("estudiante", "docente", "coordinador", "admin")


class Facultad(Base):
    __tablename__ = "facultades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True)

    programas: Mapped[list["Programa"]] = relationship(back_populates="facultad", cascade="all, delete-orphan")


class Programa(Base):
    __tablename__ = "programas"

    id: Mapped[int] = mapped_column(primary_key=True)
    facultad_id: Mapped[int] = mapped_column(ForeignKey("facultades.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(150))
    codigo: Mapped[str] = mapped_column(String(20), unique=True)

    facultad: Mapped[Facultad] = relationship(back_populates="programas")
    asignaturas: Mapped[list["Asignatura"]] = relationship(back_populates="programa", cascade="all, delete-orphan")
    resultados: Mapped[list["ResultadoAprendizaje"]] = relationship(back_populates="programa", cascade="all, delete-orphan")


# Relación muchos a muchos: resultados de aprendizaje que aporta cada asignatura
asignatura_ra = Table(
    "asignatura_ra",
    Base.metadata,
    Column("asignatura_id", ForeignKey("asignaturas.id", ondelete="CASCADE"), primary_key=True),
    Column("ra_id", ForeignKey("resultados_aprendizaje.id", ondelete="CASCADE"), primary_key=True),
)


class ResultadoAprendizaje(Base):
    """Resultado de aprendizaje del programa (Decreto 1330 de 2019)."""

    __tablename__ = "resultados_aprendizaje"
    __table_args__ = (UniqueConstraint("programa_id", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    programa_id: Mapped[int] = mapped_column(ForeignKey("programas.id", ondelete="CASCADE"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))  # p. ej. "RA1"
    descripcion: Mapped[str] = mapped_column(Text)

    programa: Mapped[Programa] = relationship(back_populates="resultados")


class Asignatura(Base):
    __tablename__ = "asignaturas"

    id: Mapped[int] = mapped_column(primary_key=True)
    programa_id: Mapped[int] = mapped_column(ForeignKey("programas.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(150))
    codigo: Mapped[str] = mapped_column(String(20))
    semestre: Mapped[int] = mapped_column(Integer, default=1)

    programa: Mapped[Programa] = relationship(back_populates="asignaturas")
    resultados: Mapped[list[ResultadoAprendizaje]] = relationship(secondary=asignatura_ra)
    grupos: Mapped[list["Grupo"]] = relationship(back_populates="asignatura", cascade="all, delete-orphan")


class Grupo(Base):
    """Grupo (curso) de una asignatura en un periodo, a cargo de un docente."""

    __tablename__ = "grupos"

    id: Mapped[int] = mapped_column(primary_key=True)
    asignatura_id: Mapped[int] = mapped_column(ForeignKey("asignaturas.id", ondelete="CASCADE"), index=True)
    docente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    periodo: Mapped[str] = mapped_column(String(10))  # p. ej. "2026-2"
    nombre: Mapped[str] = mapped_column(String(100))
    codigo_ingreso: Mapped[str] = mapped_column(String(6), unique=True, index=True, default=generar_codigo)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    asignatura: Mapped[Asignatura] = relationship(back_populates="grupos")
    docente: Mapped[Usuario] = relationship(foreign_keys=[docente_id])
    matriculas: Mapped[list["Matricula"]] = relationship(back_populates="grupo", cascade="all, delete-orphan")


class Matricula(Base):
    __tablename__ = "matriculas"
    __table_args__ = (UniqueConstraint("grupo_id", "estudiante_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id", ondelete="CASCADE"), index=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    grupo: Mapped[Grupo] = relationship(back_populates="matriculas")
    estudiante: Mapped[Usuario] = relationship(foreign_keys=[estudiante_id])


class AlertaSeguimiento(Base):
    """Registro de que una alerta temprana fue atendida; no se vuelve a mostrar hasta que aparezca un motivo nuevo."""

    __tablename__ = "alertas_seguimiento"

    id: Mapped[int] = mapped_column(primary_key=True)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id", ondelete="CASCADE"), index=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    atendido_por_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    motivos: Mapped[str] = mapped_column(String(200))  # códigos separados por coma
    nota: Mapped[str] = mapped_column(Text, default="")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


# ---------- Sprint 7: clase en vivo y notificaciones ----------

class SesionVivo(Base):
    """Sesión de clase en vivo (estilo Kahoot) lanzada por un docente desde uno de sus cuestionarios."""

    __tablename__ = "sesiones_vivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    cuestionario_id: Mapped[int] = mapped_column(ForeignKey("cuestionarios.id", ondelete="CASCADE"), index=True)
    docente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    pin: Mapped[str] = mapped_column(String(6), index=True)  # único solo entre sesiones activas
    estado: Mapped[str] = mapped_column(String(25), default="lobby")  # lobby | pregunta | resultados_pregunta | finalizada
    pregunta_actual: Mapped[int] = mapped_column(Integer, default=-1)  # índice en el orden del cuestionario
    segundos_por_pregunta: Mapped[int] = mapped_column(Integer, default=30)
    inicio_pregunta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    actividad_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    finalizada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cuestionario: Mapped[Cuestionario] = relationship()
    participantes: Mapped[list["ParticipanteVivo"]] = relationship(cascade="all, delete-orphan")


class ParticipanteVivo(Base):
    __tablename__ = "participantes_vivo"
    __table_args__ = (UniqueConstraint("sesion_id", "apodo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sesion_id: Mapped[int] = mapped_column(ForeignKey("sesiones_vivo.id", ondelete="CASCADE"), index=True)
    apodo: Mapped[str] = mapped_column(String(20))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=lambda: secrets.token_urlsafe(24))
    puntaje: Mapped[int] = mapped_column(Integer, default=0)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class RespuestaVivo(Base):
    __tablename__ = "respuestas_vivo"
    __table_args__ = (UniqueConstraint("participante_id", "pregunta_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sesion_id: Mapped[int] = mapped_column(ForeignKey("sesiones_vivo.id", ondelete="CASCADE"), index=True)
    participante_id: Mapped[int] = mapped_column(ForeignKey("participantes_vivo.id", ondelete="CASCADE"), index=True)
    pregunta_id: Mapped[int] = mapped_column(Integer, index=True)
    respuesta: Mapped[str] = mapped_column(Text)
    correcta: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # nulo en preguntas abiertas
    ms_respuesta: Mapped[int] = mapped_column(Integer, default=0)
    puntos: Mapped[int] = mapped_column(Integer, default=0)


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[str] = mapped_column(String(30))  # publicado | repaso | alerta | clase_vivo
    titulo: Mapped[str] = mapped_column(String(150))
    mensaje: Mapped[str] = mapped_column(Text, default="")
    enlace: Mapped[str] = mapped_column(String(200), default="")
    leida: Mapped[bool] = mapped_column(Boolean, default=False)
    clave: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)  # evita duplicados
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


# ---------- Sprint 8: tutor IA, banco de preguntas ----------

class ConversacionTutor(Base):
    """Conversación de un usuario con el tutor IA sobre un cuestionario (la última creada es la activa)."""

    __tablename__ = "conversaciones_tutor"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    cuestionario_id: Mapped[int] = mapped_column(ForeignKey("cuestionarios.id", ondelete="CASCADE"), index=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    mensajes: Mapped[list["MensajeTutor"]] = relationship(
        back_populates="conversacion", order_by="MensajeTutor.id", cascade="all, delete-orphan"
    )


class MensajeTutor(Base):
    __tablename__ = "mensajes_tutor"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversacion_id: Mapped[int] = mapped_column(ForeignKey("conversaciones_tutor.id", ondelete="CASCADE"), index=True)
    rol: Mapped[str] = mapped_column(String(10))  # usuario | tutor
    texto: Mapped[str] = mapped_column(Text)
    citas_json: Mapped[str] = mapped_column(Text, default="[]")  # [{marca_tiempo, fragmento}]
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora, index=True)

    conversacion: Mapped[ConversacionTutor] = relationship(back_populates="mensajes")


class PreguntaBanco(Base):
    """Pregunta guardada en el banco institucional (copia independiente del cuestionario de origen)."""

    __tablename__ = "banco_preguntas"

    id: Mapped[int] = mapped_column(primary_key=True)
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    visibilidad: Mapped[str] = mapped_column(String(15), default="institucional")  # institucional | privada
    tipo: Mapped[str] = mapped_column(String(30))
    enunciado: Mapped[str] = mapped_column(Text)
    opciones_json: Mapped[str] = mapped_column(Text, default="[]")
    respuesta_correcta: Mapped[str] = mapped_column(Text)
    explicacion: Mapped[str] = mapped_column(Text, default="")
    nivel_bloom: Mapped[str | None] = mapped_column(String(15), nullable=True)
    ra_codigo: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    ra_descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    asignatura_nombre: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    etiquetas_json: Mapped[str] = mapped_column(Text, default="[]")
    verificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    autor: Mapped[Usuario] = relationship()
