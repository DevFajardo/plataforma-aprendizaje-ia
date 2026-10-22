"""API FastAPI de la Plataforma de Aprendizaje Activo con IA."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import update

from app.config import settings
from app.db import SessionLocal, crear_tablas
from app.modelos import Tarea
from app.routers import (
    admin,
    auth,
    comparar,
    coordinacion,
    cuestionarios,
    cursos,
    docente,
    estadisticas,
    intentos,
    medios,
    procesar,
    sus,
)
from app.services.ia import proveedores_configurados

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _cerrar_tareas_huerfanas() -> None:
    """Tareas que quedaron a medias por un reinicio del servidor pasan a error."""
    with SessionLocal() as db:
        r = db.execute(
            update(Tarea)
            .where(Tarea.estado.in_(["pendiente", "transcribiendo", "generando"]))
            .values(estado="error", mensaje="Interrumpida por reinicio del servidor. Vuelve a intentarlo.")
        )
        db.commit()
        if r.rowcount:
            logging.getLogger(__name__).warning("%d tarea(s) interrumpida(s) marcadas como error", r.rowcount)


@asynccontextmanager
async def lifespan(_: FastAPI):
    crear_tablas()
    _cerrar_tareas_huerfanas()
    yield


app = FastAPI(title="Plataforma de Aprendizaje Activo con IA", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origenes_cors,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(procesar.router)
app.include_router(cuestionarios.router)
app.include_router(intentos.router)
app.include_router(docente.router)
app.include_router(comparar.router)
app.include_router(medios.router)
app.include_router(estadisticas.router)
app.include_router(sus.router)
app.include_router(admin.router)
app.include_router(cursos.router)
app.include_router(coordinacion.router)


@app.get("/api/salud")
def salud():
    return {"estado": "ok", "proveedores": proveedores_configurados(), "orden": settings.lista_proveedores}
