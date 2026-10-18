"""Modelos SQLAlchemy 2.0."""
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
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
    rol: Mapped[str] = mapped_column(String(20), default="estudiante")  # estudiante | docente
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

    video: Mapped[Video] = relationship()
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
