"""Pruebas del Sprint 5: Vimeo, rechazo de en vivo/duración, repaso diferido (retención), grupo control,
comparación de grupos, tiempo del docente y datos personales (Ley 1581 de 2012)."""
import json
import statistics
import sys
import types
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, select, text

from app import db as modulo_db
from app.config import settings
from app.modelos import Cuestionario, Intento, Repaso, Usuario, Video, ahora
from app.services.estadistica import d_de_cohen, interpretar_d
from app.services.transcripcion import (
    _descargar_audio,
    extraer_video_id,
    hash_vimeo,
    identificar_video,
    verificar_video_procesable,
)
from tests.conftest import PASSWORD, _registrar

URL_VIMEO = "https://vimeo.com/76979871"


# ---------- Utilidades ----------

def configurar_repaso(cliente, docente, cid, dias=7):
    r = cliente.patch(f"/api/cuestionarios/{cid}", json={"repaso_dias": dias}, headers=docente)
    assert r.status_code == 200, r.text


def publicar(cliente, docente, cid, **extra):
    r = cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True, **extra}, headers=docente)
    assert r.status_code == 200, r.text


def vencer_repasos(sesion_factory):
    """Simula el paso del tiempo: todos los repasos pasan a estar vencidos."""
    with sesion_factory() as db:
        for r in db.scalars(select(Repaso)).all():
            r.disponible_desde = ahora() - timedelta(minutes=1)
        db.commit()


def respuestas_correctas():
    return {"opcion_multiple": "B", "verdadero_falso": "Verdadero", "abierta": "algo"}


# ---------- Vimeo: identificar_video ----------

@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://www.youtube.com/shorts/dQw4w9WgXcQ",
])
def test_identificar_video_youtube(url):
    assert identificar_video(url) == ("youtube", "dQw4w9WgXcQ")


@pytest.mark.parametrize("url", [
    "https://vimeo.com/76979871",
    "https://www.vimeo.com/76979871",
    "https://vimeo.com/channels/staffpicks/76979871",
    "https://player.vimeo.com/video/76979871",
    "https://player.vimeo.com/video/76979871?h=abcdef1234",
    "https://vimeo.com/76979871/abcdef1234",
    "https://vimeo.com/groups/nombre/videos/76979871",
])
def test_identificar_video_vimeo(url):
    assert identificar_video(url) == ("vimeo", "76979871")


@pytest.mark.parametrize("url", [
    "https://vimeo.com/",
    "https://vimeo.com/channels/staffpicks",
    "https://example.com/76979871",
    "https://dailymotion.com/video/x7tgad0",
    "no es una url",
    "",
])
def test_identificar_video_invalidos(url):
    with pytest.raises(ValueError):
        identificar_video(url)


def test_hash_vimeo_en_no_listados_y_extraer_video_id_sigue_siendo_de_youtube():
    assert hash_vimeo("https://vimeo.com/76979871/abcdef1234") == "abcdef1234"
    assert hash_vimeo("https://player.vimeo.com/video/76979871?h=abcdef1234") == "abcdef1234"
    assert hash_vimeo(URL_VIMEO) is None
    with pytest.raises(ValueError):
        extraer_video_id(URL_VIMEO)


def test_procesar_vimeo_y_cache_por_plataforma_e_id(cliente, docente, crear_cuestionario, sesion_factory, monkeypatch):
    from app.routers import procesar

    llamadas = []
    original = procesar.obtener_transcripcion
    monkeypatch.setattr(procesar, "obtener_transcripcion", lambda url: llamadas.append(url) or original(url))
    c1 = crear_cuestionario(docente, "https://vimeo.com/76979871/abcdef1234")
    c2 = crear_cuestionario(docente, "https://player.vimeo.com/video/76979871")
    assert len(llamadas) == 1  # la segunda vez se reutiliza la transcripción
    d = cliente.get(f"/api/cuestionarios/{c1}", headers=docente).json()
    assert d["medio"] == "vimeo" and d["video_externo_id"] == "76979871"
    assert d["vimeo_hash"] == "abcdef1234" and d["youtube_id"] is None
    with sesion_factory() as db:
        v = db.scalars(select(Video)).all()
        assert len(v) == 1 and v[0].plataforma == "vimeo"
    assert c1 != c2


def test_procesar_rechaza_url_de_otra_plataforma(cliente, docente):
    r = cliente.post("/api/procesar", json={"url": "https://dailymotion.com/video/x7tgad0", "num_preguntas": 3}, headers=docente)
    assert r.status_code == 400


# ---------- Rechazo de transmisiones en vivo y videos largos ----------

def _yt_dlp_falso(monkeypatch, info, descargas):
    class _YDL:
        def __init__(self, opciones):
            self.opciones = opciones

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download=True):
            assert download is False  # primero solo metadatos
            return info

        def process_ie_result(self, i, download=True):
            descargas.append(i)
            (self_carpeta / "audio.mp3").write_bytes(b"x")

    self_carpeta = None
    monkeypatch.setitem(sys.modules, "yt_dlp", types.SimpleNamespace(YoutubeDL=_YDL))

    def fijar(carpeta):
        nonlocal self_carpeta
        self_carpeta = carpeta

    return fijar


@pytest.mark.parametrize("info", [
    {"is_live": True, "duration": None},
    {"live_status": "is_upcoming"},
    {"live_status": "is_live"},
    {"live_status": "post_live"},
])
def test_rechaza_transmisiones_en_vivo(monkeypatch, tmp_path, info):
    descargas = []
    _yt_dlp_falso(monkeypatch, info, descargas)(tmp_path)
    with pytest.raises(RuntimeError, match="transmisiones en vivo ni estrenos programados"):
        _descargar_audio("https://vimeo.com/1", tmp_path)
    assert descargas == []  # nunca se descargó el audio


def test_rechaza_video_demasiado_largo(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "max_duracion_min", 180)
    descargas = []
    _yt_dlp_falso(monkeypatch, {"duration": 181 * 60, "live_status": "not_live"}, descargas)(tmp_path)
    with pytest.raises(RuntimeError, match="máximo permitido es 180 min"):
        _descargar_audio("https://vimeo.com/1", tmp_path)
    assert descargas == []


def test_video_normal_se_descarga(monkeypatch, tmp_path):
    descargas = []
    _yt_dlp_falso(monkeypatch, {"duration": 600, "live_status": "not_live"}, descargas)(tmp_path)
    assert _descargar_audio("https://vimeo.com/1", tmp_path).name == "audio.mp3"
    assert len(descargas) == 1


def test_duracion_maxima_es_configurable():
    verificar_video_procesable({"duration": 170 * 60})  # dentro del límite por defecto (180)
    with pytest.raises(RuntimeError):
        settings.max_duracion_min = 60
        try:
            verificar_video_procesable({"duration": 61 * 60})
        finally:
            settings.max_duracion_min = 180


def test_mensaje_de_error_en_vivo_llega_a_la_tarea(cliente, docente, monkeypatch):
    from app.routers import procesar

    def _falla(url):
        raise RuntimeError("No se procesan transmisiones en vivo ni estrenos programados; usa un video ya publicado.")

    monkeypatch.setattr(procesar, "obtener_transcripcion", _falla)
    r = cliente.post("/api/procesar", json={"url": URL_VIMEO, "num_preguntas": 3}, headers=docente)
    t = cliente.get(f"/api/tareas/{r.json()['id']}", headers=docente).json()
    assert t["estado"] == "error" and "transmisiones en vivo" in t["mensaje"]


# ---------- Repaso diferido ----------

def test_repaso_diferido_flujo_completo(cliente, docente, estudiante, crear_cuestionario, intentar, sesion_factory):
    cid = crear_cuestionario(docente)
    configurar_repaso(cliente, docente, cid, 7)
    publicar(cliente, docente, cid)

    inicial = intentar(estudiante, cid, correctas=1)
    assert inicial["tipo"] == "inicial" and inicial["repaso_disponible_desde"] is not None
    assert cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).json()["repaso"]["vencido"] is False

    # Antes de la fecha: el repaso es "próximo" y los nuevos intentos son de práctica
    pendientes = cliente.get("/api/repasos", headers=estudiante).json()
    assert len(pendientes) == 1 and pendientes[0]["vencido"] is False and pendientes[0]["cuestionario_id"] == cid
    assert intentar(estudiante, cid, correctas=2)["tipo"] == "practica"

    # Vence el repaso: el siguiente intento es diferido y no da retroalimentación por pregunta
    vencer_repasos(sesion_factory)
    assert cliente.get("/api/repasos", headers=estudiante).json()[0]["vencido"] is True
    creado = cliente.post(f"/api/cuestionarios/{cid}/intentos", headers=estudiante).json()
    assert creado["tipo"] == "diferido" and creado["con_feedback"] is False
    c = cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).json()
    for p in c["preguntas"]:
        r = cliente.post(f"/api/intentos/{creado['id']}/responder",
                         json={"pregunta_id": p["id"], "respuesta": respuestas_correctas()[p["tipo"]]}, headers=estudiante)
        assert r.status_code == 200
        assert r.json() == {"registrada": True, "con_feedback": False, "correcta": None,
                            "respuesta_correcta": "", "explicacion": "", "marca_tiempo": ""}
    fin = cliente.post(f"/api/intentos/{creado['id']}/finalizar", headers=estudiante).json()
    assert fin["tipo"] == "diferido" and fin["puntaje"] == 2
    # Al finalizar sí se muestran las respuestas correctas
    assert len(fin["revision"]) == 3 and fin["revision"][0]["respuesta_correcta"] == "B"
    assert fin["revision"][0]["explicacion"] == "Porque sí."

    # El repaso queda completado y los siguientes intentos vuelven a ser de práctica
    assert cliente.get("/api/repasos", headers=estudiante).json() == []
    assert intentar(estudiante, cid)["tipo"] == "practica"
    with sesion_factory() as db:
        assert db.scalars(select(Repaso)).one().completado_intento_id == creado["id"]


def test_sin_repaso_dias_no_se_crea_repaso(cliente, docente, estudiante, crear_cuestionario, intentar, sesion_factory):
    cid = crear_cuestionario(docente)
    publicar(cliente, docente, cid)
    r = intentar(estudiante, cid)
    assert r["tipo"] == "inicial" and r["repaso_disponible_desde"] is None
    with sesion_factory() as db:
        assert db.scalars(select(Repaso)).all() == []
    assert cliente.get("/api/repasos", headers=estudiante).json() == []


def test_el_creador_no_recibe_repasos(cliente, docente, crear_cuestionario, intentar, sesion_factory):
    cid = crear_cuestionario(docente)
    configurar_repaso(cliente, docente, cid, 3)
    assert intentar(docente, cid)["tipo"] == "inicial"
    with sesion_factory() as db:
        assert db.scalars(select(Repaso)).all() == []


def test_repaso_dias_solo_admite_1_3_7_14(cliente, docente, crear_cuestionario):
    cid = crear_cuestionario(docente)
    for ok in (1, 3, 7, 14):
        configurar_repaso(cliente, docente, cid, ok)
    for mal in (0, 2, 30):
        assert cliente.patch(f"/api/cuestionarios/{cid}", json={"repaso_dias": mal}, headers=docente).status_code == 422
    # null explícito quita el repaso
    assert cliente.patch(f"/api/cuestionarios/{cid}", json={"repaso_dias": None}, headers=docente).json()["repaso_dias"] is None


def test_intentos_inicial_y_practica_se_asignan_al_finalizar(cliente, docente, estudiante, crear_cuestionario, intentar):
    cid = crear_cuestionario(docente)
    publicar(cliente, docente, cid)
    # Dos intentos abiertos a la vez: solo el primero que se finaliza es "inicial"
    a = cliente.post(f"/api/cuestionarios/{cid}/intentos", headers=estudiante).json()["id"]
    b = cliente.post(f"/api/cuestionarios/{cid}/intentos", headers=estudiante).json()["id"]
    assert cliente.post(f"/api/intentos/{b}/finalizar", headers=estudiante).json()["tipo"] == "inicial"
    assert cliente.post(f"/api/intentos/{a}/finalizar", headers=estudiante).json()["tipo"] == "practica"


# ---------- Retención ----------

def _ciclo_retencion(cliente, docente, estudiante, crear_cuestionario, intentar, sesion_factory, ini, dif):
    cid = crear_cuestionario(docente)
    configurar_repaso(cliente, docente, cid, 1)
    publicar(cliente, docente, cid)
    intentar(estudiante, cid, correctas=ini)
    vencer_repasos(sesion_factory)
    intentar(estudiante, cid, correctas=dif)
    return cid


def test_retencion_en_resultados_y_csv(cliente, docente, estudiante, crear_cuestionario, intentar, sesion_factory):
    cid = _ciclo_retencion(cliente, docente, estudiante, crear_cuestionario, intentar, sesion_factory, 2, 1)
    r = cliente.get(f"/api/cuestionarios/{cid}/resultados", headers=docente).json()
    ret = r["retencion"]
    assert ret["estudiantes"] == 1 and ret["repaso_dias"] == 1
    assert ret["promedio_inicial"] == 100.0 and ret["promedio_diferido"] == 50.0
    assert ret["retencion_pct"] == 50.0 and ret["diferencia_puntos"] == -50.0
    assert ret["detalle"][0]["retencion"] == 50.0
    # el diferido no cuenta como "último intento" de la ganancia de aprendizaje
    assert r["ganancia"]["estudiantes"] == 0
    assert {i["tipo"] for i in r["intentos"]} == {"inicial", "diferido"}

    csv = cliente.get(f"/api/cuestionarios/{cid}/resultados.csv", headers=docente).content.decode("utf-8-sig")
    assert "Consentimiento investigación" in csv.splitlines()[0]
    assert "Retención (intento inicial vs. intento diferido a 1 días)" in csv
    assert "Retención % (diferido / inicial x 100),50.0" in csv


def test_retencion_vacia_sin_diferido(cliente, docente, estudiante, crear_cuestionario, intentar):
    cid = crear_cuestionario(docente)
    publicar(cliente, docente, cid)
    intentar(estudiante, cid)
    ret = cliente.get(f"/api/cuestionarios/{cid}/resultados", headers=docente).json()["retencion"]
    assert ret["estudiantes"] == 0 and ret["retencion_pct"] is None


def test_estadisticas_del_estudiante_incluyen_su_retencion(cliente, docente, estudiante, crear_cuestionario, intentar, sesion_factory):
    _ciclo_retencion(cliente, docente, estudiante, crear_cuestionario, intentar, sesion_factory, 2, 1)
    e = cliente.get("/api/estadisticas/yo", headers=estudiante).json()
    assert e["retencion_promedio"] == 50.0
    assert cliente.get("/api/estadisticas/yo", headers=docente).json()["retencion_promedio"] is None


# ---------- Modo grupo control ----------

def test_duplicar_crea_borrador_control_con_preguntas(cliente, docente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(docente)
    configurar_repaso(cliente, docente, cid, 7)
    publicar(cliente, docente, cid)
    r = cliente.post(f"/api/cuestionarios/{cid}/duplicar", json={"modo": "control"}, headers=docente)
    assert r.status_code == 201, r.text
    copia = cliente.get(f"/api/cuestionarios/{r.json()['id']}", headers=docente).json()
    original = cliente.get(f"/api/cuestionarios/{cid}", headers=docente).json()
    assert copia["modo"] == "control" and copia["publicado"] is False
    assert copia["codigo_compartir"] != original["codigo_compartir"]
    assert copia["repaso_dias"] == 7 and copia["titulo"].endswith("(grupo control)")
    assert [p["enunciado"] for p in copia["preguntas"]] == [p["enunciado"] for p in original["preguntas"]]
    assert {p["id"] for p in copia["preguntas"]}.isdisjoint({p["id"] for p in original["preguntas"]})
    # Un borrador no es visible para estudiantes
    assert cliente.get(f"/api/cuestionarios/{copia['id']}", headers=estudiante).status_code == 403
    # Título personalizado
    r2 = cliente.post(f"/api/cuestionarios/{cid}/duplicar", json={"modo": "control", "titulo": "Mi control"}, headers=docente)
    assert r2.json()["titulo"] == "Mi control"


def test_duplicar_solo_el_docente_creador(cliente, docente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(docente)
    otro = _registrar(cliente, "docente", "Otro", "otro@prueba.com")
    assert cliente.post(f"/api/cuestionarios/{cid}/duplicar", json={"modo": "control"}, headers=otro).status_code == 403
    assert cliente.post(f"/api/cuestionarios/{cid}/duplicar", json={"modo": "control"}, headers=estudiante).status_code == 403
    assert cliente.post(f"/api/cuestionarios/{cid}/duplicar", json={"modo": "raro"}, headers=docente).status_code == 422


def test_modo_control_sin_resumen_ni_feedback(cliente, docente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(docente)
    control = cliente.post(f"/api/cuestionarios/{cid}/duplicar", json={"modo": "control"}, headers=docente).json()["id"]
    publicar(cliente, docente, control)

    visto = cliente.get(f"/api/cuestionarios/{control}", headers=estudiante).json()
    assert visto["modo"] == "control" and visto["resumen"] == "" and visto["ideas_clave"] == []
    assert all(p["marca_tiempo"] == "" for p in visto["preguntas"])
    # El docente sí ve el contenido completo
    propio = cliente.get(f"/api/cuestionarios/{control}", headers=docente).json()
    assert propio["resumen"] == "Resumen de prueba." and propio["ideas_clave"] == ["Idea 1", "Idea 2"]

    creado = cliente.post(f"/api/cuestionarios/{control}/intentos", headers=estudiante).json()
    assert creado["tipo"] == "inicial" and creado["con_feedback"] is False
    for p in visto["preguntas"]:
        r = cliente.post(f"/api/intentos/{creado['id']}/responder",
                         json={"pregunta_id": p["id"], "respuesta": respuestas_correctas()[p["tipo"]]}, headers=estudiante)
        assert r.json()["con_feedback"] is False and r.json()["explicacion"] == "" and r.json()["correcta"] is None
    fin = cliente.post(f"/api/intentos/{creado['id']}/finalizar", headers=estudiante).json()
    assert fin["puntaje"] == 2 and fin["total"] == 2
    assert fin["revision"] is None  # solo el puntaje


def test_modo_aprendizaje_si_da_feedback(cliente, docente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(docente)
    publicar(cliente, docente, cid)
    creado = cliente.post(f"/api/cuestionarios/{cid}/intentos", headers=estudiante).json()
    assert creado["con_feedback"] is True
    p = cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).json()["preguntas"][0]
    r = cliente.post(f"/api/intentos/{creado['id']}/responder", json={"pregunta_id": p["id"], "respuesta": "B"}, headers=estudiante).json()
    assert r["correcta"] is True and r["explicacion"] == "Porque sí."


# ---------- Comparación de grupos ----------

def _escenario_comparacion(cliente, docente, crear_cuestionario, intentar, sesion_factory, consentimientos=(True,) * 6):
    """Grupo A (aprendizaje) y B (control) con 3 estudiantes cada uno; devuelve (a, b)."""
    a = crear_cuestionario(docente)
    configurar_repaso(cliente, docente, a, 1)
    b = cliente.post(f"/api/cuestionarios/{a}/duplicar", json={"modo": "control"}, headers=docente).json()["id"]
    publicar(cliente, docente, a)
    publicar(cliente, docente, b)
    est = [
        _registrar(cliente, "estudiante", f"Persona {n}", f"p{n}@prueba.com", investigacion=consentimientos[n])
        for n in range(6)
    ]
    for h, ini in zip(est[:3], (2, 2, 1)):
        intentar(h, a, correctas=ini)  # A inicial: 100, 100, 50
    for h, ini in zip(est[3:], (1, 0, 1)):
        intentar(h, b, correctas=ini)  # B inicial: 50, 0, 50
    vencer_repasos(sesion_factory)
    for h, dif in zip(est[:3], (2, 1, 2)):
        intentar(h, a, correctas=dif)  # A diferido: 100, 50, 100
    for h, dif in zip(est[3:], (1, 1, 0)):
        intentar(h, b, correctas=dif)  # B diferido: 50, 50, 0
    return a, b


def test_comparar_calcula_media_desviacion_y_d_de_cohen(cliente, docente, crear_cuestionario, intentar, sesion_factory):
    a, b = _escenario_comparacion(cliente, docente, crear_cuestionario, intentar, sesion_factory)
    r = cliente.get(f"/api/comparar?a={a}&b={b}", headers=docente)
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["a"]["modo"] == "aprendizaje" and r["b"]["modo"] == "control"
    # Intento inicial: A = [100, 100, 50], B = [50, 0, 50]
    assert r["a"]["inicial"] == {"n": 3, "media": 83.33, "desviacion": 28.87}
    assert r["b"]["inicial"] == {"n": 3, "media": 33.33, "desviacion": 28.87}
    assert r["efecto_inicial"]["diferencia_medias"] == 50.0
    assert r["efecto_inicial"]["d_cohen"] == 1.73
    assert "grande" in r["efecto_inicial"]["interpretacion"] and "A supera a B" in r["efecto_inicial"]["interpretacion"]
    # Diferido: A = [100, 50, 100], B = [50, 50, 0]
    assert r["a"]["diferido"]["media"] == 83.33 and r["b"]["diferido"]["media"] == 33.33
    # Retención por estudiante: A = [100, 50, 200]; B = [100, 0] (el estudiante con inicial 0 % no tiene retención)
    esperado_a = [100.0, 50.0, 200.0]
    assert r["a"]["retencion"]["media"] == round(statistics.fmean(esperado_a), 2)
    assert r["a"]["retencion"]["desviacion"] == round(statistics.stdev(esperado_a), 2)
    assert r["b"]["retencion"] == {"n": 2, "media": 50.0, "desviacion": 70.71}
    assert r["efecto_retencion"]["d_cohen"] == round(d_de_cohen(esperado_a, [100.0, 0.0]), 2)
    assert "prueba t de Welch" in r["nota"]


def test_comparar_permisos_y_validaciones(cliente, docente, estudiante, crear_cuestionario):
    a = crear_cuestionario(docente)
    b = cliente.post(f"/api/cuestionarios/{a}/duplicar", json={"modo": "control"}, headers=docente).json()["id"]
    otro = _registrar(cliente, "docente", "Otro", "otro@prueba.com")
    assert cliente.get(f"/api/comparar?a={a}&b={b}", headers=estudiante).status_code == 403
    assert cliente.get(f"/api/comparar?a={a}&b={b}", headers=otro).status_code == 403
    assert cliente.get(f"/api/comparar?a={a}&b={a}", headers=docente).status_code == 400
    assert cliente.get(f"/api/comparar?a={a}&b=9999", headers=docente).status_code == 404
    assert cliente.get(f"/api/comparar.csv?a={a}&b={b}", headers=otro).status_code == 403
    assert cliente.get(f"/api/comparar?a={a}&b={b}").status_code == 401


def test_comparar_sin_datos_no_falla(cliente, docente, crear_cuestionario):
    a = crear_cuestionario(docente)
    b = cliente.post(f"/api/cuestionarios/{a}/duplicar", json={"modo": "control"}, headers=docente).json()["id"]
    r = cliente.get(f"/api/comparar?a={a}&b={b}", headers=docente).json()
    assert r["a"]["inicial"] == {"n": 0, "media": None, "desviacion": None}
    assert r["efecto_inicial"]["d_cohen"] is None and "No se puede calcular" in r["efecto_inicial"]["interpretacion"]


@pytest.mark.parametrize("d,texto", [(0.0, "trivial"), (0.19, "trivial"), (0.2, "pequeño"), (-0.49, "pequeño"),
                                      (0.5, "mediano"), (0.79, "mediano"), (0.8, "grande"), (-2.0, "grande")])
def test_interpretacion_de_cohen(d, texto):
    assert texto in interpretar_d(d)


def test_comparar_csv_solo_con_consentimiento_y_anonimo(cliente, docente, crear_cuestionario, intentar, sesion_factory):
    # Las personas 2 y 4 no aceptaron participar en el estudio
    consentimientos = (True, True, False, True, False, True)
    a, b = _escenario_comparacion(cliente, docente, crear_cuestionario, intentar, sesion_factory, consentimientos)
    csv = cliente.get(f"/api/comparar.csv?a={a}&b={b}", headers=docente).content.decode("utf-8-sig")
    filas = csv.strip().splitlines()
    assert filas[0] == "Grupo,Modo,Estudiante,Inicial (%),Diferido (%),Retención (%)"
    assert len(filas) == 1 + 4  # 4 estudiantes con consentimiento
    assert filas[1].startswith("A,aprendizaje,E1,100.0,100.0,100.0")
    assert all(f.split(",")[2] in ("E1", "E2", "E3", "E4") for f in filas[1:])
    assert "Persona" not in csv and "@prueba.com" not in csv


# ---------- Tiempo del docente ----------

def test_tiempo_edicion_se_acumula_y_valida(cliente, docente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(docente)
    url = f"/api/cuestionarios/{cid}/tiempo-edicion"
    assert cliente.post(url, json={"segundos": 90}, headers=docente).json()["segundos_edicion"] == 90
    assert cliente.post(url, json={"segundos": 30}, headers=docente).json()["segundos_edicion"] == 120
    assert cliente.post(url, json={"segundos": 4 * 3600}, headers=docente).status_code == 200
    assert cliente.post(url, json={"segundos": 4 * 3600 + 1}, headers=docente).status_code == 422
    assert cliente.post(url, json={"segundos": 0}, headers=docente).status_code == 422
    assert cliente.post(url, json={"segundos": -5}, headers=docente).status_code == 422
    assert cliente.post(url, json={"segundos": 10}, headers=estudiante).status_code == 403
    otro = _registrar(cliente, "docente", "Otro", "otro@prueba.com")
    assert cliente.post(url, json={"segundos": 10}, headers=otro).status_code == 403
    assert cliente.get(f"/api/cuestionarios/{cid}", headers=docente).json()["segundos_edicion"] == 120 + 4 * 3600


def test_ahorro_de_tiempo_del_docente(cliente, docente, crear_cuestionario, sesion_factory):
    cid = crear_cuestionario(docente)
    sin_estimar = crear_cuestionario(docente)  # no cuenta: no tiene estimación
    with sesion_factory() as db:
        db.get(Cuestionario, cid).segundos_generacion = 120  # 2 min de generación
        db.commit()
    cliente.post(f"/api/cuestionarios/{cid}/tiempo-edicion", json={"segundos": 180}, headers=docente)  # 3 min de edición
    cliente.post(f"/api/cuestionarios/{sin_estimar}/tiempo-edicion", json={"segundos": 3000}, headers=docente)
    publicar(cliente, docente, cid, estimacion_manual_min=20)

    d = cliente.get(f"/api/cuestionarios/{cid}", headers=docente).json()
    assert d["estimacion_manual_min"] == 20 and d["publicado_en"] is not None
    t = cliente.get("/api/estadisticas/yo", headers=docente).json()["docente"]["tiempo"]
    # herramienta = 2 + 3 = 5 min; manual = 20 min -> ahorro = 75 %
    assert t == {"cuestionarios_con_estimacion": 1, "promedio_herramienta_min": 5.0,
                 "promedio_manual_min": 20.0, "ahorro_pct": 75.0}


def test_tiempo_sin_estimaciones_y_generacion_real(cliente, docente, crear_cuestionario):
    cid = crear_cuestionario(docente)
    assert cliente.get("/api/estadisticas/yo", headers=docente).json()["docente"]["tiempo"] == {
        "cuestionarios_con_estimacion": 0, "promedio_herramienta_min": None,
        "promedio_manual_min": None, "ahorro_pct": None}
    # La estimación también se puede registrar después, desde la edición
    r = cliente.patch(f"/api/cuestionarios/{cid}", json={"estimacion_manual_min": 30}, headers=docente)
    assert r.json()["estimacion_manual_min"] == 30
    t = cliente.get("/api/estadisticas/yo", headers=docente).json()["docente"]["tiempo"]
    assert t["cuestionarios_con_estimacion"] == 1 and t["ahorro_pct"] > 99  # en pruebas la generación es instantánea


# ---------- Datos personales y consentimiento ----------

def test_registro_sin_aceptar_la_politica_es_422(cliente):
    base = {"nombre": "Ana", "email": "ana@correo.com", "password": PASSWORD}
    assert cliente.post("/api/auth/registro", json=base).status_code == 422
    r = cliente.post("/api/auth/registro", json={**base, "acepta_tratamiento_datos": False, "consentimiento_investigacion": True})
    assert r.status_code == 422
    assert "política de tratamiento de datos" in r.json()["detail"][0]["msg"]


def test_registro_guarda_consentimientos(cliente):
    base = {"nombre": "Ana", "email": "ana@correo.com", "password": PASSWORD, "acepta_tratamiento_datos": True}
    u = cliente.post("/api/auth/registro", json=base).json()["usuario"]
    assert u["acepta_tratamiento_datos"] is True and u["consentimiento_investigacion"] is False
    u2 = cliente.post("/api/auth/registro", json={**base, "email": "b@correo.com", "consentimiento_investigacion": True}).json()["usuario"]
    assert u2["consentimiento_investigacion"] is True


def test_cuenta_editar_nombre_contrasena_y_consentimiento(cliente, estudiante):
    r = cliente.patch("/api/auth/cuenta", json={"nombre": "Nuevo Nombre", "consentimiento_investigacion": False}, headers=estudiante)
    assert r.status_code == 200 and r.json()["nombre"] == "Nuevo Nombre" and r.json()["consentimiento_investigacion"] is False
    # Cambiar la contraseña exige la actual
    assert cliente.patch("/api/auth/cuenta", json={"password_nueva": "OtraClave999"}, headers=estudiante).status_code == 400
    assert cliente.patch("/api/auth/cuenta", json={"password_actual": "incorrecta", "password_nueva": "OtraClave999"},
                         headers=estudiante).status_code == 400
    assert cliente.patch("/api/auth/cuenta", json={"password_actual": PASSWORD, "password_nueva": "corta"},
                         headers=estudiante).status_code == 422
    ok = cliente.patch("/api/auth/cuenta", json={"password_actual": PASSWORD, "password_nueva": "OtraClave999"}, headers=estudiante)
    assert ok.status_code == 200
    assert cliente.post("/api/auth/login", json={"email": "estudiante@prueba.com", "password": PASSWORD}).status_code == 401
    assert cliente.post("/api/auth/login", json={"email": "estudiante@prueba.com", "password": "OtraClave999"}).status_code == 200


def test_mis_datos_incluye_todo_lo_del_usuario(cliente, docente, estudiante, crear_cuestionario, intentar):
    cid = crear_cuestionario(docente)
    publicar(cliente, docente, cid)
    intentar(estudiante, cid, correctas=1)
    cliente.post("/api/sus", json={"respuestas": [3] * 10, "comentario": "ok"}, headers=estudiante)
    datos = cliente.get("/api/auth/mis-datos", headers=estudiante).json()
    assert datos["usuario"]["email"] == "estudiante@prueba.com" and "password_hash" not in json.dumps(datos)
    assert len(datos["intentos"]) == 1 and datos["intentos"][0]["puntaje"] == 1 and len(datos["intentos"][0]["respuestas"]) == 3
    assert datos["encuesta"]["puntaje_sus"] == 50.0
    assert datos["cuestionarios"] == []
    d = cliente.get("/api/auth/mis-datos", headers=docente).json()
    assert [c["id"] for c in d["cuestionarios"]] == [cid] and d["intentos"] == [] and d["encuesta"] is None
    assert cliente.get("/api/auth/mis-datos").status_code == 401


def test_eliminar_cuenta_borra_todo(cliente, docente, estudiante, crear_cuestionario, intentar, sesion_factory, tmp_path):
    # El docente tiene un cuestionario de YouTube con repaso y otro de archivo subido
    cid = crear_cuestionario(docente)
    configurar_repaso(cliente, docente, cid, 3)
    publicar(cliente, docente, cid)
    r = cliente.post("/api/procesar/archivo", files={"archivo": ("clase.mp3", b"audio")}, data={"num_preguntas": "3"}, headers=docente)
    archivo_cid = cliente.get(f"/api/tareas/{r.json()['id']}", headers=docente).json()["cuestionario_id"]
    carpeta = tmp_path / "subidas"
    assert len(list(carpeta.iterdir())) == 1
    # El estudiante responde (crea intento y repaso) y la encuesta
    intentar(estudiante, cid)
    cliente.post("/api/sus", json={"respuestas": [5, 1] * 5}, headers=estudiante)

    # Contraseña incorrecta: no se borra nada
    assert cliente.request("DELETE", "/api/auth/cuenta", json={"password": "mala"}, headers=docente).status_code == 400

    assert cliente.request("DELETE", "/api/auth/cuenta", json={"password": PASSWORD}, headers=docente).status_code == 204
    assert list(carpeta.iterdir()) == []  # archivo subido eliminado
    assert cliente.post("/api/auth/login", json={"email": "docente@prueba.com", "password": PASSWORD}).status_code == 401
    assert cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).status_code == 404
    assert cliente.get(f"/api/cuestionarios/{archivo_cid}", headers=estudiante).status_code in (403, 404)
    with sesion_factory() as db:
        assert db.scalars(select(Cuestionario)).all() == []
        assert db.scalars(select(Repaso)).all() == []  # el repaso del estudiante dependía del cuestionario borrado
        assert db.scalars(select(Intento)).all() == []

    # Eliminar la cuenta del estudiante: intentos, encuesta y tareas desaparecen
    assert cliente.request("DELETE", "/api/auth/cuenta", json={"password": PASSWORD}, headers=estudiante).status_code == 204
    with sesion_factory() as db:
        assert db.scalars(select(Usuario)).all() == []
        for tabla in ("respuestas_sus", "tareas", "preguntas", "repasos", "intentos"):
            assert db.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar() == 0, tabla


def test_eliminar_cuenta_de_estudiante_conserva_el_cuestionario_ajeno(cliente, docente, estudiante, crear_cuestionario, intentar, sesion_factory):
    cid = crear_cuestionario(docente)
    configurar_repaso(cliente, docente, cid, 3)
    publicar(cliente, docente, cid)
    intentar(estudiante, cid)
    assert cliente.request("DELETE", "/api/auth/cuenta", json={"password": PASSWORD}, headers=estudiante).status_code == 204
    assert cliente.get(f"/api/cuestionarios/{cid}", headers=docente).status_code == 200
    with sesion_factory() as db:
        assert db.scalars(select(Intento)).all() == [] and db.scalars(select(Repaso)).all() == []
    assert cliente.get(f"/api/cuestionarios/{cid}/resultados", headers=docente).json()["total_intentos"] == 0


def test_sus_csv_solo_incluye_a_quienes_consintieron(cliente, docente):
    si = _registrar(cliente, "estudiante", "Con Consentimiento", "si@prueba.com", investigacion=True)
    no = _registrar(cliente, "estudiante", "Sin Consentimiento", "no@prueba.com", investigacion=False)
    cliente.post("/api/sus", json={"respuestas": [5, 1] * 5, "comentario": "Excelente"}, headers=si)
    cliente.post("/api/sus", json={"respuestas": [1, 5] * 5, "comentario": "Pésimo"}, headers=no)
    csv = cliente.get("/api/sus/resumen.csv", headers=docente).content.decode("utf-8-sig")
    assert "Excelente" in csv and "Pésimo" not in csv
    assert len(csv.strip().splitlines()) == 2
    # Si luego revoca su consentimiento, sale de la exportación
    cliente.patch("/api/auth/cuenta", json={"consentimiento_investigacion": False}, headers=si)
    assert len(cliente.get("/api/sus/resumen.csv", headers=docente).content.decode("utf-8-sig").strip().splitlines()) == 1


def test_resultados_csv_del_docente_incluye_a_todos_con_columna_de_consentimiento(cliente, docente, crear_cuestionario, intentar):
    cid = crear_cuestionario(docente)
    publicar(cliente, docente, cid)
    si = _registrar(cliente, "estudiante", "Acepta", "si@prueba.com", investigacion=True)
    no = _registrar(cliente, "estudiante", "Rechaza", "no@prueba.com", investigacion=False)
    intentar(si, cid)
    intentar(no, cid)
    filas = cliente.get(f"/api/cuestionarios/{cid}/resultados.csv", headers=docente).content.decode("utf-8-sig").splitlines()
    datos = {f.split(",")[0]: f.split(",")[-1] for f in filas[1:3]}
    assert datos == {"Acepta": "Sí", "Rechaza": "No"}


# ---------- Migración de la BD existente ----------

def test_migracion_rellena_columnas_de_una_bd_anterior(tmp_path, monkeypatch):
    motor = create_engine(f"sqlite:///{tmp_path / 'vieja.db'}")
    with motor.begin() as con:
        con.execute(text("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre VARCHAR(100), email VARCHAR(255), "
                         "password_hash VARCHAR(255), rol VARCHAR(20), creado_en DATETIME)"))
        con.execute(text("CREATE TABLE videos (id INTEGER PRIMARY KEY, youtube_id VARCHAR(20), url VARCHAR(500), "
                         "titulo_original VARCHAR(300), fuente_transcripcion VARCHAR(50), transcripcion_json TEXT, "
                         "archivo VARCHAR(100), creado_en DATETIME)"))
        con.execute(text("CREATE TABLE tareas (id VARCHAR(32) PRIMARY KEY, archivo VARCHAR(100))"))
        con.execute(text("CREATE TABLE cuestionarios (id INTEGER PRIMARY KEY, video_id INTEGER, creador_id INTEGER, "
                         "titulo VARCHAR(300), publicado BOOLEAN, creado_en DATETIME)"))
        con.execute(text("CREATE TABLE intentos (id INTEGER PRIMARY KEY, usuario_id INTEGER, cuestionario_id INTEGER, "
                         "finalizado BOOLEAN, creado_en DATETIME)"))
        con.execute(text("INSERT INTO usuarios VALUES (1, 'A', 'a@a.com', 'x', 'docente', '2026-01-01 00:00:00')"))
        con.execute(text("INSERT INTO videos (id, youtube_id, url, archivo) VALUES (1, 'dQw4w9WgXcQ', 'u', NULL), (2, NULL, 'a', 'f.mp3')"))
        con.execute(text("INSERT INTO cuestionarios VALUES (1, 1, 1, 't', 1, '2026-01-02 00:00:00'), (2, 1, 1, 'b', 0, '2026-01-02 00:00:00')"))
        con.execute(text("INSERT INTO intentos VALUES (1, 1, 1, 1, '2026-01-03 00:00:00'), (2, 1, 1, 1, '2026-01-04 00:00:00'), "
                         "(3, 1, 1, 0, '2026-01-05 00:00:00')"))
    monkeypatch.setattr(modulo_db, "engine", motor)
    modulo_db._migrar_columnas()
    modulo_db._migrar_columnas()  # idempotente
    with motor.connect() as con:
        assert con.execute(text("SELECT plataforma, video_externo_id FROM videos ORDER BY id")).all() == [
            ("youtube", "dQw4w9WgXcQ"), ("archivo", None)]
        assert con.execute(text("SELECT tipo FROM intentos ORDER BY id")).scalars().all() == ["inicial", "practica", "inicial"]
        assert con.execute(text("SELECT modo, repaso_dias, segundos_edicion FROM cuestionarios WHERE id = 1")).one() == ("aprendizaje", None, 0)
        assert con.execute(text("SELECT publicado_en IS NOT NULL FROM cuestionarios ORDER BY id")).scalars().all() == [1, 0]
        assert con.execute(text("SELECT acepta_tratamiento_datos, consentimiento_investigacion FROM usuarios")).one() == (0, 0)
