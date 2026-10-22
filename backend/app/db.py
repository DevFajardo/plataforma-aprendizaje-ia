"""Conexión a la base de datos (SQLite por defecto; PostgreSQL cambiando DATABASE_URL)."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

def _normalizar_url(url: str) -> str:
    """Los proveedores en la nube suelen entregar postgres:// o postgresql://; SQLAlchemy usa el driver psycopg 3."""
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


_url = _normalizar_url(settings.database_url)
_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}
engine = create_engine(_url, connect_args=_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def crear_tablas() -> None:
    from app import modelos  # noqa: F401  (registra los modelos)

    Base.metadata.create_all(bind=engine)
    _migrar_columnas()


# Columnas añadidas después del Sprint 2 (create_all no altera tablas existentes)
_COLUMNAS_NUEVAS = {
    "videos": [
        ("archivo", "VARCHAR(100)"),
        ("plataforma", "VARCHAR(20) DEFAULT 'youtube'"),
        ("video_externo_id", "VARCHAR(40)"),
    ],
    "tareas": [("archivo", "VARCHAR(100)")],
    "usuarios": [
        ("acepta_tratamiento_datos", "BOOLEAN DEFAULT FALSE"),
        ("consentimiento_investigacion", "BOOLEAN DEFAULT FALSE"),
        ("consentimiento_fecha", "TIMESTAMP"),
        ("programa_id", "INTEGER"),
    ],
    "cuestionarios": [
        ("modo", "VARCHAR(20) DEFAULT 'aprendizaje'"),
        ("repaso_dias", "INTEGER"),
        ("segundos_generacion", "INTEGER DEFAULT 0"),
        ("segundos_edicion", "INTEGER DEFAULT 0"),
        ("publicado_en", "TIMESTAMP"),
        ("estimacion_manual_min", "INTEGER"),
        ("grupo_id", "INTEGER"),
    ],
    "preguntas": [
        ("ra_id", "INTEGER"),
        ("nivel_bloom", "VARCHAR(15)"),
        ("verificacion", "TEXT"),
        ("banco_id", "INTEGER"),
    ],
    "intentos": [("tipo", "VARCHAR(10) DEFAULT 'inicial'")],
}


def _migrar_columnas() -> None:
    """Migración simple: añade las columnas que falten en tablas ya existentes y rellena los datos previos."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    anadidas: set[tuple[str, str]] = set()
    with engine.begin() as con:
        tablas = set(insp.get_table_names())
        for tabla, columnas in _COLUMNAS_NUEVAS.items():
            if tabla not in tablas:
                continue
            existentes = {c["name"] for c in insp.get_columns(tabla)}
            for nombre, tipo in columnas:
                if nombre not in existentes:
                    con.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}"))
                    anadidas.add((tabla, nombre))

        # Rellenado de los datos existentes (solo la primera vez que se añade cada columna)
        if ("videos", "plataforma") in anadidas:
            con.execute(text("UPDATE videos SET plataforma = 'archivo' WHERE archivo IS NOT NULL"))
            con.execute(text("UPDATE videos SET video_externo_id = youtube_id WHERE youtube_id IS NOT NULL"))
        if ("cuestionarios", "publicado_en") in anadidas:
            con.execute(text("UPDATE cuestionarios SET publicado_en = creado_en WHERE publicado = TRUE"))
        if ("intentos", "tipo") in anadidas:
            # El primer intento finalizado de cada usuario en cada cuestionario es "inicial"; los demás, "practica"
            filas = con.execute(
                text("SELECT id, usuario_id, cuestionario_id FROM intentos WHERE finalizado = TRUE ORDER BY creado_en, id")
            ).all()
            vistos: set[tuple[int, int]] = set()
            for intento_id, usuario_id, cuestionario_id in filas:
                if (usuario_id, cuestionario_id) in vistos:
                    con.execute(text("UPDATE intentos SET tipo = 'practica' WHERE id = :intento"), {"intento": intento_id})
                vistos.add((usuario_id, cuestionario_id))
