"""Configuración común de las pruebas.

- BD SQLite temporal por prueba (se sobrescribe `get_db` y el `SessionLocal` que usan las tareas en segundo plano).
- Transcripción e IA simuladas: las pruebas NO usan internet ni proveedores reales.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main
from app.config import settings
from app.db import Base, get_db
from app.routers import procesar
from app.services import notificaciones as notif_servicio
from app.services import vivo as servicio_vivo
from app.schemas import Pregunta, ResultadoIA, Segmento, Transcripcion

PASSWORD = "Clave12345"
URL_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def resultado_falso(num_preguntas: int = 3) -> ResultadoIA:
    """Cuestionario fijo: opción múltiple (correcta B), verdadero/falso (Verdadero) y abierta."""
    return ResultadoIA(
        titulo="Cuestionario de prueba",
        resumen="Resumen de prueba.",
        ideas_clave=["Idea 1", "Idea 2"],
        preguntas=[
            Pregunta(tipo="opcion_multiple", enunciado="¿Cuál es la capital?", opciones=["A", "B", "C", "D"],
                     respuesta_correcta="B", explicacion="Porque sí.", marca_tiempo="00:10"),
            Pregunta(tipo="verdadero_falso", enunciado="El cielo es azul.", opciones=["Verdadero", "Falso"],
                     respuesta_correcta="Verdadero", explicacion="Dispersión de Rayleigh.", marca_tiempo="00:20"),
            Pregunta(tipo="abierta", enunciado="Explica la idea principal.", opciones=[],
                     respuesta_correcta="La idea principal es X.", explicacion="Se dice al inicio.", marca_tiempo="00:30"),
        ],
    )


@pytest.fixture()
def sesion_factory(tmp_path):
    motor = create_engine(f"sqlite:///{tmp_path / 'prueba.db'}", connect_args={"check_same_thread": False})
    from app import modelos  # noqa: F401  (registra los modelos)

    Base.metadata.create_all(motor)
    yield sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)
    motor.dispose()


@pytest.fixture()
def cliente(sesion_factory, tmp_path, monkeypatch):
    def _get_db():
        db = sesion_factory()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = _get_db
    # Las tareas en segundo plano abren su propia sesión: deben usar la BD de prueba
    monkeypatch.setattr(procesar, "SessionLocal", sesion_factory)
    monkeypatch.setattr(procesar, "CARPETA_SUBIDAS", tmp_path / "subidas")
    # Clase en vivo: la BD de prueba, sin estado de otras pruebas
    monkeypatch.setattr(servicio_vivo, "SessionLocal", sesion_factory)
    servicio_vivo._sesiones.clear()
    notif_servicio._ultimo_calculo_alertas.clear()
    monkeypatch.setattr(settings, "secret_key", "clave-solo-para-pruebas-0123456789-abcdef")
    monkeypatch.setattr(settings, "limite_diario_procesamientos", 1000)

    # Simulacros: sin internet ni IA
    monkeypatch.setattr(
        procesar, "obtener_transcripcion",
        lambda url: Transcripcion(fuente="subtitulos_youtube", idioma="es", segmentos=[Segmento(inicio=0, texto="hola")]),
    )
    monkeypatch.setattr(
        procesar, "transcribir_subida",
        lambda ruta: Transcripcion(fuente="whisper_groq", idioma="es", segmentos=[Segmento(inicio=0, texto="hola")]),
    )
    monkeypatch.setattr(procesar, "generar_con_respaldo", lambda texto, n: (resultado_falso(n), "falso"))

    # Sin `with`: así no se ejecuta el lifespan (que usaría la BD real)
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def _registrar(cliente, rol: str, nombre: str, email: str, investigacion: bool = True) -> dict:
    r = cliente.post(
        "/api/auth/registro",
        json={"nombre": nombre, "email": email, "password": PASSWORD, "rol": rol,
              "acepta_tratamiento_datos": True, "consentimiento_investigacion": investigacion},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture()
def docente(cliente):
    return _registrar(cliente, "docente", "Docente Uno", "docente@prueba.com")


@pytest.fixture()
def estudiante(cliente):
    return _registrar(cliente, "estudiante", "Estudiante Uno", "estudiante@prueba.com")


@pytest.fixture()
def otro_estudiante(cliente):
    return _registrar(cliente, "estudiante", "Estudiante Dos", "estudiante2@prueba.com")


@pytest.fixture()
def crear_cuestionario(cliente):
    """Fábrica: procesa un video (simulado) y devuelve el id del cuestionario generado."""

    def _crear(headers: dict, url: str = URL_VIDEO) -> int:
        r = cliente.post("/api/procesar", json={"url": url, "num_preguntas": 3}, headers=headers)
        assert r.status_code == 200, r.text
        # TestClient ejecuta las tareas en segundo plano antes de devolver la respuesta
        t = cliente.get(f"/api/tareas/{r.json()['id']}", headers=headers).json()
        assert t["estado"] == "listo", t
        return t["cuestionario_id"]

    return _crear


@pytest.fixture()
def intentar(cliente):
    """Fábrica: realiza un intento completo. `correctas` = respuestas acertadas de las 2 preguntas cerradas."""

    def _intentar(headers: dict, cuestionario_id: int, correctas: int = 2) -> dict:
        c = cliente.get(f"/api/cuestionarios/{cuestionario_id}", headers=headers).json()
        intento = cliente.post(f"/api/cuestionarios/{cuestionario_id}/intentos", headers=headers).json()["id"]
        respuestas = {"opcion_multiple": ("B", "A"), "verdadero_falso": ("Verdadero", "Falso"), "abierta": ("texto", "texto")}
        acertadas = 0
        for p in c["preguntas"]:
            buena, mala = respuestas[p["tipo"]]
            acierta = p["tipo"] != "abierta" and acertadas < correctas
            if acierta:
                acertadas += 1
            r = cliente.post(f"/api/intentos/{intento}/responder",
                             json={"pregunta_id": p["id"], "respuesta": buena if acierta or p["tipo"] == "abierta" else mala},
                             headers=headers)
            assert r.status_code == 200, r.text
        r = cliente.post(f"/api/intentos/{intento}/finalizar", headers=headers)
        assert r.status_code == 200, r.text
        return r.json()

    return _intentar


@pytest.fixture(autouse=True)
def ia_generica(monkeypatch):
    """Simula `ejecutar_con_respaldo` (tutor, calificación de abiertas, verificación): sin internet ni IA real.

    Por defecto la IA «está caída» (lanza RuntimeError). Una prueba asigna `ia_generica["manejador"] = f(prompt, esquema)`
    para devolver un objeto del esquema pedido; `ia_generica["prompts"]` guarda los prompts recibidos.
    """
    from app.services import ia

    estado = {"manejador": None, "prompts": []}

    def falso(prompt, esquema):
        estado["prompts"].append(prompt)
        if estado["manejador"] is None:
            raise RuntimeError("IA no disponible (simulada)")
        return estado["manejador"](prompt, esquema), "falso"

    monkeypatch.setattr(ia, "ejecutar_con_respaldo", falso)
    return estado
