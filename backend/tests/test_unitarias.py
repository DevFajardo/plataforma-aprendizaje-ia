"""Pruebas unitarias: URLs de YouTube, SUS, normalización, adaptador de IA y Whisper."""
import sys
import types

import pytest

from app.config import settings
from app.routers.intentos import _normalizar
from app.schemas import ResultadoIA
from app.services import ia
from app.services.sus import calcular_puntaje, interpretar
from app.services.transcripcion import _whisper, extraer_video_id
from tests.conftest import resultado_falso

ID = "dQw4w9WgXcQ"


@pytest.mark.parametrize("url", [
    f"https://www.youtube.com/watch?v={ID}",
    f"https://youtube.com/watch?v={ID}&t=30s",
    f"https://m.youtube.com/watch?v={ID}",
    f"https://youtu.be/{ID}",
    f"https://www.youtube.com/shorts/{ID}",
    f"https://www.youtube.com/embed/{ID}",
])
def test_extraer_video_id_validos(url):
    assert extraer_video_id(url) == ID


@pytest.mark.parametrize("url", [
    "https://example.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=corto",
    "https://www.youtube.com/",
    "no es una url",
    "",
])
def test_extraer_video_id_invalidos(url):
    with pytest.raises(ValueError):
        extraer_video_id(url)


def test_sus_todo_tres_es_50():
    assert calcular_puntaje([3] * 10) == 50


def test_sus_mejor_caso_es_100():
    assert calcular_puntaje([5, 1, 5, 1, 5, 1, 5, 1, 5, 1]) == 100


def test_sus_peor_caso_es_0():
    assert calcular_puntaje([1, 5, 1, 5, 1, 5, 1, 5, 1, 5]) == 0


def test_sus_rechaza_datos_invalidos():
    with pytest.raises(ValueError):
        calcular_puntaje([3] * 9)
    with pytest.raises(ValueError):
        calcular_puntaje([6] + [3] * 9)


@pytest.mark.parametrize("puntaje,esperado", [
    (0, "Pobre"), (50.9, "Pobre"), (51, "Aceptable bajo"), (67.9, "Aceptable bajo"),
    (68, "Bueno"), (80.3, "Bueno"), (80.4, "Excelente"), (100, "Excelente"),
])
def test_sus_interpretacion(puntaje, esperado):
    assert interpretar(puntaje) == esperado


def test_normalizar_respuestas():
    assert _normalizar("  Hola   MUNDO \n") == "hola mundo"
    assert _normalizar("Verdadero") == _normalizar(" verdadero ")


# ---------- Adaptador de IA (Strategy con respaldo) ----------

class _Falla:
    nombre = "falla"

    def configurado(self):
        return True

    def generar(self, texto, n):
        raise ValueError("fallo simulado")


class _Funciona:
    nombre = "funciona"

    def configurado(self):
        return True

    def generar(self, texto, n):
        return resultado_falso(n)


class _SinClave(_Funciona):
    def configurado(self):
        return False


def test_ia_pasa_al_segundo_proveedor_si_el_primero_falla(monkeypatch):
    monkeypatch.setattr(ia, "PROVEEDORES", {"a": _Falla, "b": _Funciona})
    monkeypatch.setattr(settings, "proveedores_ia", "a,b")
    resultado, nombre = ia.generar_con_respaldo("texto", 3)
    assert nombre == "b"
    assert isinstance(resultado, ResultadoIA)


def test_ia_omite_proveedores_sin_clave(monkeypatch):
    monkeypatch.setattr(ia, "PROVEEDORES", {"a": _SinClave, "b": _Funciona})
    monkeypatch.setattr(settings, "proveedores_ia", "a,b")
    assert ia.generar_con_respaldo("texto", 3)[1] == "b"


def test_ia_todos_fallan_lanza_error(monkeypatch):
    monkeypatch.setattr(ia, "PROVEEDORES", {"a": _Falla})
    monkeypatch.setattr(settings, "proveedores_ia", "a")
    with pytest.raises(RuntimeError, match="Todos los proveedores"):
        ia.generar_con_respaldo("texto", 3)


def test_ia_reintenta_errores_transitorios(monkeypatch):
    llamadas = {"n": 0}

    class _Inestable(_Funciona):
        def generar(self, texto, n):
            llamadas["n"] += 1
            if llamadas["n"] < 3:
                raise TimeoutError("lento")
            return resultado_falso(n)

    monkeypatch.setattr(ia, "PROVEEDORES", {"a": _Inestable})
    monkeypatch.setattr(settings, "proveedores_ia", "a")
    monkeypatch.setattr(ia, "ESPERAS_REINTENTO", (0, 0))
    assert ia.generar_con_respaldo("texto", 3)[1] == "a"
    assert llamadas["n"] == 3


# ---------- Whisper: idioma configurable ----------

def _groq_falso(monkeypatch, capturado):
    class _Transcripciones:
        def create(self, **kw):
            capturado.update(kw)
            return types.SimpleNamespace(segments=[{"text": "hi", "start": 1}])

    class _Groq:
        def __init__(self, api_key):
            self.audio = types.SimpleNamespace(transcriptions=_Transcripciones())

    monkeypatch.setitem(sys.modules, "groq", types.SimpleNamespace(Groq=_Groq))


def test_whisper_sin_idioma_usa_deteccion_automatica(monkeypatch, tmp_path):
    capturado = {}
    _groq_falso(monkeypatch, capturado)
    monkeypatch.setattr(settings, "idioma_transcripcion", "")
    f = tmp_path / "a.mp3"
    f.write_bytes(b"x")
    assert _whisper(f, 0)[0].texto == "hi"
    assert "language" not in capturado


def test_whisper_con_idioma_configurado(monkeypatch, tmp_path):
    capturado = {}
    _groq_falso(monkeypatch, capturado)
    monkeypatch.setattr(settings, "idioma_transcripcion", "en")
    f = tmp_path / "a.mp3"
    f.write_bytes(b"x")
    _whisper(f, 0)
    assert capturado["language"] == "en"
