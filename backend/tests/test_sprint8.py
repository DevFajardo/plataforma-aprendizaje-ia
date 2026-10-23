"""Pruebas del Sprint 8: tutor IA, calificación de abiertas, verificación de calidad, psicometría, banco y subtítulos.

La IA está simulada con la fixture autouse `ia_generica` (por defecto «caída»)."""
import json
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.config import settings
from app.modelos import Cuestionario, MensajeTutor, Pregunta, Repaso, Usuario, Video, ahora
from app.schemas import Segmento, Transcripcion
from app.services import psicometria, subtitulos, tutor
from app.services.calificacion import CalificacionIA, calcular_puntaje, nivel_por_puntaje
from app.services.verificacion import LoteVerificacion, VerificacionPregunta
from tests.conftest import PASSWORD, _registrar


# ---------- Utilidades ----------

def cargar_transcripcion(sesion_factory, segmentos=((0, "Introducción al tema"), (65, "La fotosíntesis produce glucosa"), (272, "Conclusiones finales"))):
    with sesion_factory() as db:
        for v in db.scalars(select(Video)):
            v.transcripcion_json = Transcripcion(
                fuente="subtitulos_youtube", idioma="es", segmentos=[Segmento(inicio=i, texto=t) for i, t in segmentos]
            ).model_dump_json()
        db.commit()


def publicar(cliente, docente, cid, **extra):
    r = cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True, **extra}, headers=docente)
    assert r.status_code == 200, r.text


def responde_tutor(ia_generica, texto="Se explica en el video.", citas=()):
    ia_generica["manejador"] = lambda prompt, esquema: tutor.RespuestaTutor(
        texto=texto, citas=[tutor.CitaTutor(marca_tiempo=m, fragmento=f) for m, f in citas]
    )


def preguntar(cliente, headers, cid, texto="¿Qué es la fotosíntesis?"):
    return cliente.post(f"/api/cuestionarios/{cid}/tutor", json={"pregunta": texto}, headers=headers)


@pytest.fixture()
def cuestionario(cliente, docente, estudiante, sesion_factory, crear_cuestionario, ia_generica):
    cid = crear_cuestionario(docente)
    ia_generica["prompts"].clear()  # descarta el intento de verificación hecho al generar
    cargar_transcripcion(sesion_factory)
    publicar(cliente, docente, cid)
    return cid


def iniciar_intento(cliente, headers, cid):
    r = cliente.post(f"/api/cuestionarios/{cid}/intentos", headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def preguntas_de(cliente, headers, cid):
    return cliente.get(f"/api/cuestionarios/{cid}", headers=headers).json()["preguntas"]


# ---------- Psicometría (valores conocidos) ----------

ITEM1 = psicometria.ItemEntrada(id=1, orden=0, enunciado="Item 1", opciones=["A", "B", "C", "D"], correcta="B")
ITEM2 = psicometria.ItemEntrada(id=2, orden=1, enunciado="Item 2", opciones=["A", "B", "C"], correcta="A")
# (item 1, item 2) de 10 estudiantes; totales = [2, 2, 2, 1, 1, 1, 0, 0, 1, 1]
FILAS = [("B", "A"), ("B", "A"), ("B", "A"), ("B", "C"), ("B", "C"), ("A", "A"), ("A", "C"), ("C", "C"), ("A", "A"), ("B", "C")]
RESPUESTAS = [{1: a, 2: b} for a, b in FILAS]


def test_psicometria_dificultad():
    it1, it2 = psicometria.analizar_items([ITEM1, ITEM2], RESPUESTAS)
    assert it1.n == 10 and it1.suficiente
    assert it1.p == pytest.approx(0.6)
    assert it2.p == pytest.approx(0.5)
    assert it1.dificultad == "Dificultad adecuada"


def test_psicometria_discriminacion_27_por_ciento():
    # N = 10 -> k = round(2.7) = 3; superior = estudiantes 1-3, inferior = 10, 7 y 8
    it1, it2 = psicometria.analizar_items([ITEM1, ITEM2], RESPUESTAS)
    assert it1.d == pytest.approx(1 - 1 / 3, abs=1e-3)
    assert it2.d == pytest.approx(1.0)
    assert it2.discriminacion == "Discrimina muy bien"


def test_psicometria_punto_biserial():
    it1, _ = psicometria.analizar_items([ITEM1, ITEM2], RESPUESTAS)
    # M1 = 1,5; M0 = 0,5; s = 0,7; r = (1,5-0,5)/0,7 * raiz(0,6*0,4) = 0,6999
    assert it1.r_pb == pytest.approx(0.6999, abs=1e-3)


def test_punto_biserial_funcion_directa_y_casos_limite():
    assert psicometria.correlacion_punto_biserial([1, 2, 3, 4], [False, False, True, True]) == pytest.approx(0.8944, abs=1e-3)
    assert psicometria.correlacion_punto_biserial([1, 2, 3], [True, True, True]) is None  # sin varianza del ítem
    assert psicometria.correlacion_punto_biserial([2, 2, 2], [True, False, True]) is None  # sin varianza del total


def test_psicometria_distractor_no_funcional():
    it1, _ = psicometria.analizar_items([ITEM1, ITEM2], RESPUESTAS)
    por_letra = {d.letra: d for d in it1.distractores}
    assert por_letra["A"].porcentaje == 30.0 and por_letra["A"].funcional is True
    assert por_letra["C"].porcentaje == 10.0 and por_letra["C"].funcional is True
    assert por_letra["D"].porcentaje == 0.0 and por_letra["D"].funcional is False  # menos del 5 %
    assert por_letra["B"].correcta and por_letra["B"].funcional is None
    assert any("no funcional" in o and "D" in o for o in it1.observaciones)


def test_psicometria_datos_insuficientes():
    it1, it2 = psicometria.analizar_items([ITEM1, ITEM2], RESPUESTAS[:4])
    assert not it1.suficiente and it1.n == 4
    assert it1.p is None and it1.d is None and it1.r_pb is None and it1.distractores == []


def test_psicometria_distractor_que_confunde_a_los_mejores():
    x = psicometria.ItemEntrada(id=10, orden=0, enunciado="X", opciones=["A", "B", "C"], correcta="A")
    ys = [psicometria.ItemEntrada(id=20 + k, orden=1 + k, enunciado=f"Y{k}", opciones=["a", "b"], correcta="a") for k in range(3)]
    mejores = {10: "C", 20: "a", 21: "a", 22: "a"}   # aciertan todo menos X (eligen C)
    medios = {10: "A", 20: "a", 21: "a", 22: "b"}
    peores = {10: "A", 20: "b", 21: "b", 22: "b"}
    res = psicometria.analizar_items([x, *ys], [mejores, mejores, medios, medios, peores, peores])
    item = res[0]
    assert item.n == 6
    c = next(d for d in item.distractores if d.letra == "C")
    assert c.confunde_mejores and item.revisar
    assert any("la opción C confunde a los mejores" in o for o in item.observaciones)
    assert item.d is not None and item.d < 0
    assert item.discriminacion == "Discriminación negativa"


@pytest.mark.parametrize("p,texto", [(0.9, "Muy fácil"), (0.75, "Fácil"), (0.5, "Dificultad adecuada"), (0.2, "Difícil"), (0.05, "Muy difícil")])
def test_interpretacion_dificultad(p, texto):
    assert psicometria.interpretar_dificultad(p) == texto


def test_resultados_incluyen_analisis_de_items(cliente, docente, cuestionario, intentar):
    estudiantes = [_registrar(cliente, "estudiante", f"Est {i}", f"est{i}@prueba.com") for i in range(5)]
    for i, h in enumerate(estudiantes):
        intentar(h, cuestionario, correctas=2 if i < 3 else 1)
    r = cliente.get(f"/api/cuestionarios/{cuestionario}/resultados", headers=docente).json()
    assert r["items_minimo"] == 5 and r["items_intentos"] == 5
    assert len(r["items"]) == 2  # solo preguntas cerradas
    assert all(i["suficiente"] and i["n"] == 5 for i in r["items"])
    assert r["items"][0]["p"] is not None and r["items"][0]["distractores"]


def test_resultados_pocas_respuestas_son_datos_insuficientes(cliente, docente, estudiante, cuestionario, intentar):
    intentar(estudiante, cuestionario)
    r = cliente.get(f"/api/cuestionarios/{cuestionario}/resultados", headers=docente).json()
    assert all(not i["suficiente"] and i["p"] is None for i in r["items"])


def test_pdf_de_resultados_con_analisis_de_items(cliente, docente, estudiante, cuestionario, intentar):
    intentar(estudiante, cuestionario)
    r = cliente.get(f"/api/cuestionarios/{cuestionario}/reporte.pdf", headers=docente)
    assert r.status_code == 200 and r.content.startswith(b"%PDF")


# ---------- Puntaje con abiertas aprobadas ----------

class _P:
    def __init__(self, id, tipo):
        self.id, self.tipo = id, tipo


def test_calcular_puntaje_sin_abiertas_aprobadas_es_como_antes():
    preguntas = [_P(1, "opcion_multiple"), _P(2, "verdadero_falso"), _P(3, "abierta")]
    respuestas = [{"pregunta_id": 1, "correcta": True}, {"pregunta_id": 2, "correcta": False}, {"pregunta_id": 3, "correcta": None, "ia": {"puntaje": 90}}]
    assert calcular_puntaje(respuestas, preguntas) == (1, 2)


def test_calcular_puntaje_con_abierta_aprobada_pondera_por_la_nota():
    preguntas = [_P(1, "opcion_multiple"), _P(2, "verdadero_falso"), _P(3, "abierta")]
    respuestas = [{"pregunta_id": 1, "correcta": True}, {"pregunta_id": 2, "correcta": True}, {"pregunta_id": 3, "correcta": None, "nota_final": 60}]
    assert calcular_puntaje(respuestas, preguntas) == (3, 3)  # round(2 + 0,6) = 3
    respuestas[2]["nota_final"] = 20
    assert calcular_puntaje(respuestas, preguntas) == (2, 3)  # round(2 + 0,2) = 2


@pytest.mark.parametrize("nota,nivel", [(0, "insuficiente"), (39, "insuficiente"), (40, "basico"), (69, "basico"), (70, "bueno"), (89, "bueno"), (90, "excelente"), (100, "excelente")])
def test_nivel_por_puntaje(nota, nivel):
    assert nivel_por_puntaje(nota) == nivel


# ---------- Calificación de preguntas abiertas con IA ----------

def ia_califica(ia_generica, puntaje=80):
    ia_generica["manejador"] = lambda prompt, esquema: CalificacionIA(
        puntaje=puntaje, nivel="excelente", retroalimentacion="Buena síntesis.", falto="Mencionar un ejemplo."
    )


def responder_todo(cliente, headers, cid, abierta="La idea principal es X, básicamente."):
    intento = iniciar_intento(cliente, headers, cid)
    salida = {}
    for p in preguntas_de(cliente, headers, cid):
        resp = {"opcion_multiple": "B", "verdadero_falso": "Verdadero", "abierta": abierta}[p["tipo"]]
        r = cliente.post(f"/api/intentos/{intento}/responder", json={"pregunta_id": p["id"], "respuesta": resp}, headers=headers)
        assert r.status_code == 200, r.text
        salida[p["tipo"]] = r.json()
    return intento, salida


def test_abierta_recibe_calificacion_sugerida_y_nivel_coherente(cliente, estudiante, cuestionario, ia_generica):
    ia_califica(ia_generica, 80)
    _, resp = responder_todo(cliente, estudiante, cuestionario)
    cal = resp["abierta"]["calificacion_ia"]
    assert cal["puntaje"] == 80 and cal["nivel"] == "bueno"  # el nivel sale del puntaje, no del modelo
    assert cal["retroalimentacion"] and cal["falto"]
    assert "calificacion_ia" not in resp["opcion_multiple"]


def test_prompt_de_calificacion_incluye_rubrica_y_modelo(cliente, estudiante, cuestionario, ia_generica):
    ia_califica(ia_generica)
    responder_todo(cliente, estudiante, cuestionario, abierta="Mi respuesta única")
    prompt = ia_generica["prompts"][-1]
    assert "La idea principal es X." in prompt and "Mi respuesta única" in prompt and "RÚBRICA" in prompt


def test_abierta_vacia_es_cero_sin_llamar_a_la_ia(cliente, estudiante, cuestionario, ia_generica):
    _, resp = responder_todo(cliente, estudiante, cuestionario, abierta="   ")
    assert resp["abierta"]["calificacion_ia"]["puntaje"] == 0
    assert ia_generica["prompts"] == []


def test_ia_caida_no_bloquea_la_respuesta_abierta(cliente, estudiante, cuestionario):
    _, resp = responder_todo(cliente, estudiante, cuestionario)
    assert "calificacion_ia" not in resp["abierta"]
    assert resp["abierta"]["respuesta_correcta"] == "La idea principal es X."


def test_no_hay_calificacion_visible_en_modo_control(cliente, docente, estudiante, cuestionario, ia_generica):
    ia_califica(ia_generica)
    copia = cliente.post(f"/api/cuestionarios/{cuestionario}/duplicar", json={"modo": "control"}, headers=docente).json()["id"]
    publicar(cliente, docente, copia)
    intento, resp = responder_todo(cliente, estudiante, copia)
    assert resp["abierta"]["con_feedback"] is False and "calificacion_ia" not in resp["abierta"]
    # pero queda guardada como sugerida para el docente
    cliente.post(f"/api/intentos/{intento}/finalizar", headers=estudiante)
    res = cliente.get(f"/api/cuestionarios/{copia}/resultados", headers=docente).json()
    abierta = next(p for p in res["preguntas"] if p["tipo"] == "abierta")
    assert abierta["respuestas_abiertas"][0]["sugerida"]["puntaje"] == 80


def test_docente_ve_sugerida_y_aprueba_la_nota(cliente, docente, estudiante, cuestionario, ia_generica):
    ia_califica(ia_generica, 80)
    intento, _ = responder_todo(cliente, estudiante, cuestionario)
    fin = cliente.post(f"/api/intentos/{intento}/finalizar", headers=estudiante).json()
    assert (fin["puntaje"], fin["total"]) == (2, 2)  # sin nota aprobada la abierta no cuenta, como antes

    res = cliente.get(f"/api/cuestionarios/{cuestionario}/resultados", headers=docente).json()
    abierta = next(p for p in res["preguntas"] if p["tipo"] == "abierta")
    ra = abierta["respuestas_abiertas"][0]
    assert ra["sugerida"]["puntaje"] == 80 and ra["nota_final"] is None and ra["intento_id"] == intento

    r = cliente.put(f"/api/intentos/{intento}/abiertas/{abierta['pregunta_id']}/nota", json={"nota": 80}, headers=docente)
    assert r.status_code == 200, r.text
    assert (r.json()["puntaje"], r.json()["total"]) == (3, 3)  # round(2 + 0,8)
    res = cliente.get(f"/api/cuestionarios/{cuestionario}/resultados", headers=docente).json()
    assert res["intentos"][0]["puntaje"] == 3 and res["intentos"][0]["total"] == 3
    assert next(p for p in res["preguntas"] if p["tipo"] == "abierta")["respuestas_abiertas"][0]["nota_final"] == 80


def test_docente_puede_ajustar_la_nota_a_la_baja(cliente, docente, estudiante, cuestionario, ia_generica):
    ia_califica(ia_generica, 90)
    intento, _ = responder_todo(cliente, estudiante, cuestionario)
    cliente.post(f"/api/intentos/{intento}/finalizar", headers=estudiante)
    pid = next(p["id"] for p in preguntas_de(cliente, docente, cuestionario) if p["tipo"] == "abierta")
    r = cliente.put(f"/api/intentos/{intento}/abiertas/{pid}/nota", json={"nota": 10}, headers=docente).json()
    assert (r["puntaje"], r["total"]) == (2, 3)
    assert cliente.put(f"/api/intentos/{intento}/abiertas/{pid}/nota", json={"nota": 101}, headers=docente).status_code == 422


def test_solo_el_docente_creador_aprueba_notas(cliente, docente, estudiante, cuestionario, ia_generica):
    ia_califica(ia_generica)
    intento, _ = responder_todo(cliente, estudiante, cuestionario)
    pid = next(p["id"] for p in preguntas_de(cliente, docente, cuestionario) if p["tipo"] == "abierta")
    url = f"/api/intentos/{intento}/abiertas/{pid}/nota"
    assert cliente.put(url, json={"nota": 50}, headers=estudiante).status_code == 403
    otro = _registrar(cliente, "docente", "Otro Docente", "otro@prueba.com")
    assert cliente.put(url, json={"nota": 50}, headers=otro).status_code == 403
    pid_cerrada = next(p["id"] for p in preguntas_de(cliente, docente, cuestionario) if p["tipo"] == "opcion_multiple")
    assert cliente.put(f"/api/intentos/{intento}/abiertas/{pid_cerrada}/nota", json={"nota": 50}, headers=docente).status_code == 404


# ---------- Verificación de calidad ----------

def lote_verificacion(estados):
    def manejador(prompt, esquema):
        assert esquema is LoteVerificacion
        return LoteVerificacion(preguntas=[
            VerificacionPregunta(numero=i + 1, respaldo=r, cita="fragmento", marca_tiempo="01:05",
                                 respuesta_inequivoca=ok, problemas=[] if not mal else ["Redacción ambigua"])
            for i, (r, ok, mal) in enumerate(estados)
        ])
    return manejador


def test_verificacion_se_guarda_al_generar(cliente, docente, ia_generica, crear_cuestionario):
    ia_generica["manejador"] = lote_verificacion([("si", True, False), ("parcial", True, False), ("no", False, True)])
    cid = crear_cuestionario(docente)
    p = preguntas_de(cliente, docente, cid)
    assert [x["verificacion"]["estado"] for x in p] == ["verificada", "revisar", "revisar"]
    assert p[0]["verificacion"]["cita"] == "fragmento" and p[0]["verificacion"]["marca_tiempo"] == "01:05"
    assert p[2]["verificacion"]["problemas"] == ["Redacción ambigua"]


def test_verificacion_con_ia_caida_no_bloquea(cliente, docente, crear_cuestionario):
    cid = crear_cuestionario(docente)  # la IA genérica está caída: debe quedar listo igualmente
    p = preguntas_de(cliente, docente, cid)
    assert len(p) == 3 and all(x["verificacion"] is None for x in p)


def test_estudiante_no_ve_la_verificacion(cliente, docente, estudiante, ia_generica, crear_cuestionario):
    ia_generica["manejador"] = lote_verificacion([("si", True, False)] * 3)
    cid = crear_cuestionario(docente)
    publicar(cliente, docente, cid)
    assert all(x["verificacion"] is None for x in preguntas_de(cliente, estudiante, cid))


def test_reverificar_manual_y_error_503(cliente, docente, ia_generica, crear_cuestionario):
    cid = crear_cuestionario(docente)
    assert cliente.post(f"/api/cuestionarios/{cid}/verificar", headers=docente).status_code == 503
    ia_generica["manejador"] = lote_verificacion([("si", True, False)] * 3)
    r = cliente.post(f"/api/cuestionarios/{cid}/verificar", headers=docente)
    assert r.status_code == 200 and r.json() == {"verificadas": 3, "total": 3}


def test_editar_el_contenido_invalida_la_verificacion_pero_la_explicacion_no(cliente, docente, ia_generica, crear_cuestionario):
    ia_generica["manejador"] = lote_verificacion([("si", True, False)] * 3)
    cid = crear_cuestionario(docente)
    p = next(x for x in preguntas_de(cliente, docente, cid) if x["tipo"] == "opcion_multiple")
    base = {"tipo": "opcion_multiple", "enunciado": p["enunciado"], "opciones": p["opciones"],
            "respuesta_correcta": p["respuesta_correcta"], "explicacion": "Otra explicación", "marca_tiempo": p["marca_tiempo"]}
    r = cliente.put(f"/api/preguntas/{p['id']}", json=base, headers=docente).json()
    assert r["verificacion"]["estado"] == "verificada"
    r = cliente.put(f"/api/preguntas/{p['id']}", json={**base, "enunciado": "Enunciado nuevo"}, headers=docente).json()
    assert r["verificacion"] is None


# ---------- Tutor IA ----------

def test_contexto_completo_lleva_marcas_de_tiempo():
    t = Transcripcion(fuente="subtitulos_youtube", idioma="es", segmentos=[Segmento(inicio=0, texto="Hola"), Segmento(inicio=272, texto="Adiós")])
    assert tutor.construir_contexto(t, "cualquier cosa") == "[00:00] Hola\n[04:32] Adiós"


def test_contexto_largo_selecciona_segmentos_por_palabras_clave():
    segs = [Segmento(inicio=i * 10, texto=f"relleno número {i} sin relación alguna" if i != 7 else "la mitocondria produce energía celular") for i in range(100)]
    t = Transcripcion(fuente="subtitulos_youtube", idioma="es", segmentos=segs)
    ctx = tutor.construir_contexto(t, "¿Qué hace la mitocondria?", maximo=400)
    assert len(ctx) <= 400
    assert "[01:10] la mitocondria produce energía celular" in ctx
    marcas = [l[:7] for l in ctx.splitlines()]
    assert marcas == sorted(marcas)  # en orden cronológico


def test_tutor_responde_con_citas_validas(cliente, estudiante, cuestionario, ia_generica):
    responde_tutor(ia_generica, "La fotosíntesis produce glucosa.", [
        ("01:05", "La fotosíntesis produce glucosa"),
        ("99:59", "Cita fuera del video"),   # más allá de la duración
        ("minuto uno", "Marca inválida"),
        ("01:05", "Duplicada"),
        ("4:32", "Conclusiones finales"),
    ])
    r = preguntar(cliente, estudiante, cuestionario)
    assert r.status_code == 200, r.text
    citas = r.json()["tutor"]["citas"]
    assert citas == [{"marca_tiempo": "01:05", "fragmento": "La fotosíntesis produce glucosa"},
                     {"marca_tiempo": "04:32", "fragmento": "Conclusiones finales"}]
    assert r.json()["usuario"]["rol"] == "usuario" and r.json()["restantes"] == settings.limite_tutor_diario - 1


def test_prompt_del_tutor_lleva_transcripcion_y_reglas(cliente, estudiante, cuestionario, ia_generica):
    responde_tutor(ia_generica)
    preguntar(cliente, estudiante, cuestionario, "¿Qué dice del tema?")
    prompt = ia_generica["prompts"][-1]
    assert "[01:05] La fotosíntesis produce glucosa" in prompt
    assert "SOLO con base en la transcripción" in prompt and "Eso no se explica en este video" in prompt
    assert "¿Qué dice del tema?" in prompt


def test_tutor_no_pasa_respuestas_de_preguntas_pendientes(cliente, estudiante, cuestionario, ia_generica):
    responde_tutor(ia_generica)
    intento = iniciar_intento(cliente, estudiante, cuestionario)
    p = preguntas_de(cliente, estudiante, cuestionario)
    cliente.post(f"/api/intentos/{intento}/responder", json={"pregunta_id": p[0]["id"], "respuesta": "B"}, headers=estudiante)
    preguntar(cliente, estudiante, cuestionario)
    prompt = ia_generica["prompts"][-1]
    pendientes = prompt.split("aún no las ha respondido:")[1].split("Regla estricta")[0]
    assert "El cielo es azul." in pendientes and "Explica la idea principal." in pendientes   # pendientes: solo enunciados
    assert "¿Cuál es la capital?" not in pendientes                                          # ya respondida
    # nunca viajan respuestas correctas, explicaciones ni opciones de las pendientes
    for secreto in ("La idea principal es X.", "Dispersión de Rayleigh", "Se dice al inicio", "Falso"):
        assert secreto not in prompt
    assert "NUNCA des" in prompt


def test_sin_intento_en_curso_no_hay_restricciones_de_pendientes(cliente, estudiante, cuestionario, ia_generica):
    responde_tutor(ia_generica)
    preguntar(cliente, estudiante, cuestionario)
    assert "aún no las ha respondido" not in ia_generica["prompts"][-1]


def test_tutor_bloqueado_en_modo_control(cliente, docente, estudiante, cuestionario, ia_generica):
    responde_tutor(ia_generica)
    copia = cliente.post(f"/api/cuestionarios/{cuestionario}/duplicar", json={"modo": "control"}, headers=docente).json()["id"]
    publicar(cliente, docente, copia)
    assert preguntar(cliente, estudiante, copia).status_code == 403
    estado = cliente.get(f"/api/cuestionarios/{copia}/tutor", headers=estudiante).json()
    assert estado["habilitado"] is False and "control" in estado["motivo"]
    assert ia_generica["prompts"] == []


def test_tutor_bloqueado_en_repaso_diferido(cliente, docente, estudiante, cuestionario, intentar, ia_generica, sesion_factory):
    responde_tutor(ia_generica)
    cliente.patch(f"/api/cuestionarios/{cuestionario}", json={"repaso_dias": 1}, headers=docente)
    intentar(estudiante, cuestionario)
    assert preguntar(cliente, estudiante, cuestionario).status_code == 200  # aún no vence el repaso
    with sesion_factory() as db:
        for r in db.scalars(select(Repaso)):
            r.disponible_desde = ahora() - timedelta(minutes=1)
        db.commit()
    assert preguntar(cliente, estudiante, cuestionario).status_code == 403
    estado = cliente.get(f"/api/cuestionarios/{cuestionario}/tutor", headers=estudiante).json()
    assert estado["habilitado"] is False and "diferido" in estado["motivo"]
    # y con un intento diferido en curso también
    assert iniciar_intento(cliente, estudiante, cuestionario)
    assert preguntar(cliente, estudiante, cuestionario).status_code == 403


def test_limite_diario_del_tutor(cliente, estudiante, cuestionario, ia_generica, monkeypatch):
    monkeypatch.setattr(settings, "limite_tutor_diario", 2)
    responde_tutor(ia_generica)
    assert preguntar(cliente, estudiante, cuestionario).json()["restantes"] == 1
    assert preguntar(cliente, estudiante, cuestionario).json()["restantes"] == 0
    r = preguntar(cliente, estudiante, cuestionario)
    assert r.status_code == 429 and "límite" in r.json()["detail"]
    assert cliente.get(f"/api/cuestionarios/{cuestionario}/tutor", headers=estudiante).json()["restantes"] == 0


def test_limite_diario_es_por_usuario(cliente, estudiante, otro_estudiante, cuestionario, ia_generica, monkeypatch):
    monkeypatch.setattr(settings, "limite_tutor_diario", 1)
    responde_tutor(ia_generica)
    assert preguntar(cliente, estudiante, cuestionario).status_code == 200
    assert preguntar(cliente, estudiante, cuestionario).status_code == 429
    assert preguntar(cliente, otro_estudiante, cuestionario).status_code == 200


def test_historial_solo_los_ultimos_6_mensajes(cliente, estudiante, cuestionario, ia_generica):
    responde_tutor(ia_generica, "respuesta del tutor")
    for k in range(5):
        preguntar(cliente, estudiante, cuestionario, f"pregunta número {k}")
    preguntar(cliente, estudiante, cuestionario, "pregunta final")
    prompt = ia_generica["prompts"][-1]
    previa = prompt.split("CONVERSACIÓN PREVIA:")[1].split("PREGUNTA ACTUAL")[0]
    assert previa.count("Estudiante:") == 3 and previa.count("Tutor:") == 3
    assert "pregunta número 0" not in previa and "pregunta número 1" not in previa and "pregunta número 4" in previa


def test_persistencia_y_nueva_conversacion(cliente, estudiante, cuestionario, ia_generica):
    responde_tutor(ia_generica, "respuesta")
    preguntar(cliente, estudiante, cuestionario, "primera")
    estado = cliente.get(f"/api/cuestionarios/{cuestionario}/tutor", headers=estudiante).json()
    assert [m["texto"] for m in estado["mensajes"]] == ["primera", "respuesta"]
    nueva = cliente.post(f"/api/cuestionarios/{cuestionario}/tutor/nueva", headers=estudiante)
    assert nueva.status_code == 201 and nueva.json()["mensajes"] == []
    assert nueva.json()["conversacion_id"] != estado["conversacion_id"]
    preguntar(cliente, estudiante, cuestionario, "segunda")
    assert "primera" not in ia_generica["prompts"][-1].split("PREGUNTA ACTUAL")[0].split("CONVERSACIÓN PREVIA:")[1]


def test_conversaciones_son_privadas_por_usuario(cliente, estudiante, otro_estudiante, cuestionario, ia_generica):
    responde_tutor(ia_generica)
    preguntar(cliente, estudiante, cuestionario, "secreto")
    assert cliente.get(f"/api/cuestionarios/{cuestionario}/tutor", headers=otro_estudiante).json()["mensajes"] == []


def test_ia_caida_devuelve_503_y_no_guarda_ni_cuenta(cliente, estudiante, cuestionario, sesion_factory):
    r = preguntar(cliente, estudiante, cuestionario)
    assert r.status_code == 503
    with sesion_factory() as db:
        assert db.scalars(select(MensajeTutor)).first() is None
    assert cliente.get(f"/api/cuestionarios/{cuestionario}/tutor", headers=estudiante).json()["restantes"] == settings.limite_tutor_diario


def test_tutor_no_disponible_para_cuestionario_no_publicado(cliente, docente, estudiante, crear_cuestionario, ia_generica):
    responde_tutor(ia_generica)
    cid = crear_cuestionario(docente)  # sin publicar
    assert preguntar(cliente, estudiante, cid).status_code == 403
    assert preguntar(cliente, docente, cid).status_code == 200


def test_sugerencias_iniciales_son_tres_y_sin_ia(cliente, estudiante, cuestionario, ia_generica):
    estado = cliente.get(f"/api/cuestionarios/{cuestionario}/tutor", headers=estudiante).json()
    assert len(estado["sugerencias"]) == 3 and "Idea 1" in estado["sugerencias"][0]
    assert ia_generica["prompts"] == []


def test_pregunta_vacia_o_demasiado_larga(cliente, estudiante, cuestionario, ia_generica):
    responde_tutor(ia_generica)
    assert preguntar(cliente, estudiante, cuestionario, "   ").status_code == 422
    assert preguntar(cliente, estudiante, cuestionario, "x" * 1001).status_code == 422


# ---------- Banco de preguntas ----------

def guardar_banco(cliente, headers, cid, indice=0, **datos):
    p = preguntas_de(cliente, headers, cid)[indice]
    return cliente.post(f"/api/preguntas/{p['id']}/banco", json=datos, headers=headers)


def test_guardar_en_el_banco_copia_la_pregunta(cliente, docente, cuestionario):
    r = guardar_banco(cliente, docente, cuestionario, etiquetas=["Biología", " biología ", "unidad 1"], asignatura_nombre="Biología I")
    assert r.status_code == 201, r.text
    b = r.json()
    assert b["enunciado"] == "¿Cuál es la capital?" and b["opciones"] == ["A", "B", "C", "D"]
    assert b["visibilidad"] == "institucional" and b["es_mia"] and b["autor"] == "Docente Uno"
    assert b["etiquetas"] == ["Biología", "unidad 1"] and b["asignatura_nombre"] == "Biología I"
    assert b["estado_verificacion"] == "sin_verificar"
    assert guardar_banco(cliente, docente, cuestionario).status_code == 409  # ya está en el banco


def test_visibilidad_institucional_y_privada(cliente, docente, cuestionario):
    otro = _registrar(cliente, "docente", "Otro Docente", "otro@prueba.com")
    guardar_banco(cliente, docente, cuestionario, 0, visibilidad="institucional")
    guardar_banco(cliente, docente, cuestionario, 1, visibilidad="privada")
    de_otro = cliente.get("/api/banco", headers=otro).json()
    assert de_otro["total"] == 1 and de_otro["items"][0]["enunciado"] == "¿Cuál es la capital?" and not de_otro["items"][0]["es_mia"]
    assert cliente.get("/api/banco", headers=docente).json()["total"] == 2
    privada = next(i for i in cliente.get("/api/banco", headers=docente).json()["items"] if i["visibilidad"] == "privada")
    assert cliente.patch(f"/api/banco/{privada['id']}", json={"etiquetas": ["x"]}, headers=otro).status_code == 404
    assert cliente.post(f"/api/banco/{privada['id']}/agregar", json={"cuestionario_id": 1}, headers=otro).status_code == 404


def test_solo_docentes_y_coordinadores_acceden_al_banco(cliente, estudiante, docente, sesion_factory):
    assert cliente.get("/api/banco", headers=estudiante).status_code == 403
    with sesion_factory() as db:
        u = db.scalar(select(Usuario).where(Usuario.email == "docente@prueba.com"))
        u.rol = "coordinador"
        db.commit()
    assert cliente.get("/api/banco", headers=docente).status_code == 200


def test_busqueda_y_filtros_del_banco(cliente, docente, cuestionario):
    guardar_banco(cliente, docente, cuestionario, 0)
    guardar_banco(cliente, docente, cuestionario, 1)
    guardar_banco(cliente, docente, cuestionario, 2, etiquetas=["abiertas"])
    hallar = lambda **q: cliente.get("/api/banco", params=q, headers=docente).json()
    assert hallar(q="capital")["total"] == 1
    assert hallar(q="CIELO azul")["total"] == 1
    assert hallar(q="abiertas")["total"] == 1                       # busca también en etiquetas
    assert hallar(q="inexistente")["total"] == 0
    assert hallar(tipo="verdadero_falso")["total"] == 1
    assert hallar(verificacion="sin_verificar")["total"] == 3
    assert hallar(verificacion="revisar")["total"] == 0
    assert hallar(solo_mias="true")["total"] == 3
    assert cliente.get("/api/banco", params={"verificacion": "otra"}, headers=docente).status_code == 422


def test_filtro_por_verificacion_y_bloom(cliente, docente, ia_generica, crear_cuestionario):
    ia_generica["manejador"] = lote_verificacion([("si", True, False), ("no", False, True), ("si", True, False)])
    cid = crear_cuestionario(docente)
    p = preguntas_de(cliente, docente, cid)
    cliente.put(f"/api/preguntas/{p[0]['id']}", json={"tipo": "opcion_multiple", "enunciado": p[0]["enunciado"], "opciones": p[0]["opciones"],
                                                       "respuesta_correcta": p[0]["respuesta_correcta"], "nivel_bloom": "aplicar"}, headers=docente)
    for i in range(3):
        guardar_banco(cliente, docente, cid, i)
    hallar = lambda **q: cliente.get("/api/banco", params=q, headers=docente).json()
    assert hallar(verificacion="verificada")["total"] == 2   # la primera se editó sin cambiar contenido: sigue verificada
    assert hallar(verificacion="revisar")["total"] == 1
    assert hallar(bloom="aplicar")["total"] == 1
    assert cliente.get("/api/banco/filtros", headers=docente).status_code == 200


def test_agregar_desde_el_banco_a_un_cuestionario_propio(cliente, docente, crear_cuestionario, cuestionario):
    otro = _registrar(cliente, "docente", "Otro Docente", "otro@prueba.com")
    banco = guardar_banco(cliente, docente, cuestionario, 1).json()
    propio = crear_cuestionario(otro)
    r = cliente.post(f"/api/banco/{banco['id']}/agregar", json={"cuestionario_id": propio}, headers=otro)
    assert r.status_code == 201 and r.json()["num_preguntas"] == 4
    nuevas = preguntas_de(cliente, otro, propio)
    assert len(nuevas) == 4 and nuevas[-1]["enunciado"] == "El cielo es azul." and nuevas[-1]["banco_id"] == banco["id"]
    assert nuevas[-1]["orden"] == 3
    # no se puede agregar a un cuestionario ajeno
    assert cliente.post(f"/api/banco/{banco['id']}/agregar", json={"cuestionario_id": cuestionario}, headers=otro).status_code == 403


def test_estadisticas_acumuladas_del_banco(cliente, docente, estudiante, otro_estudiante, cuestionario, intentar):
    banco = guardar_banco(cliente, docente, cuestionario, 0).json()   # opción múltiple, correcta B
    intentar(estudiante, cuestionario, correctas=2)
    intentar(otro_estudiante, cuestionario, correctas=0)
    item = cliente.get("/api/banco", headers=docente).json()["items"][0]
    assert item["id"] == banco["id"]
    assert item["estadisticas"] == {"respuestas": 2, "porcentaje_acierto": 50.0, "usos": 1}


def test_solo_el_autor_edita_o_elimina_del_banco(cliente, docente, cuestionario):
    otro = _registrar(cliente, "docente", "Otro Docente", "otro@prueba.com")
    b = guardar_banco(cliente, docente, cuestionario).json()
    assert cliente.patch(f"/api/banco/{b['id']}", json={"visibilidad": "privada"}, headers=otro).status_code == 403
    assert cliente.delete(f"/api/banco/{b['id']}", headers=otro).status_code == 403
    assert cliente.patch(f"/api/banco/{b['id']}", json={"visibilidad": "privada"}, headers=docente).json()["visibilidad"] == "privada"
    assert cliente.delete(f"/api/banco/{b['id']}", headers=docente).status_code == 204
    assert cliente.get("/api/banco", headers=docente).json()["total"] == 0
    assert preguntas_de(cliente, docente, cuestionario)[0]["banco_id"] is None
    assert guardar_banco(cliente, docente, cuestionario).status_code == 201  # se puede volver a guardar


def test_no_se_guarda_en_el_banco_una_pregunta_ajena(cliente, docente, cuestionario):
    otro = _registrar(cliente, "docente", "Otro Docente", "otro@prueba.com")
    pid = preguntas_de(cliente, docente, cuestionario)[0]["id"]
    assert cliente.post(f"/api/preguntas/{pid}/banco", json={}, headers=otro).status_code == 403


# ---------- Subtítulos y transcripción ----------

def test_vtt_tiene_cabecera_y_formato_de_tiempos():
    t = Transcripcion(fuente="whisper_groq", idioma="es", segmentos=[
        Segmento(inicio=1.0, texto="Hola a todos"), Segmento(inicio=3.5, texto="Esto & aquello <b>"), Segmento(inicio=3725.25, texto="Final --> raro")])
    vtt = subtitulos.a_vtt(t)
    lineas = vtt.splitlines()
    assert lineas[0] == "WEBVTT" and lineas[1] == ""
    assert "00:00:01.000 --> 00:00:03.500" in lineas
    assert "00:00:03.500 --> 00:00:11.500" in lineas      # sin siguiente cercano: máximo 8 s
    assert "01:02:05.250 --> 01:02:09.250" in lineas       # último: 4 s; horas con 2 dígitos
    assert "Esto &amp; aquello &lt;b&gt;" in lineas and "Final --&gt; raro" in lineas
    assert vtt.count("-->") == 3


def test_endpoint_vtt_y_texto(cliente, docente, estudiante, cuestionario):
    with_video = cliente.get(f"/api/cuestionarios/{cuestionario}", headers=estudiante).json()["video_id"]
    r = cliente.get(f"/api/videos/{with_video}/subtitulos.vtt", headers=estudiante)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/vtt")
    assert r.text.startswith("WEBVTT") and "00:01:05.000 --> 00:04:32.000" not in r.text and "00:01:05.000 --> 00:01:13.000" in r.text
    t = cliente.get(f"/api/videos/{with_video}/transcripcion.txt", headers=estudiante)
    assert t.status_code == 200 and "[01:05] La fotosíntesis produce glucosa" in t.text
    assert "attachment" in t.headers["content-disposition"]
    j = cliente.get(f"/api/videos/{with_video}/transcripcion", headers=estudiante).json()
    assert j["segmentos"][1] == {"inicio": 65, "texto": "La fotosíntesis produce glucosa"}


def test_subtitulos_requieren_acceso_al_cuestionario(cliente, docente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(docente)   # sin publicar
    vid = cliente.get(f"/api/cuestionarios/{cid}", headers=docente).json()["video_id"]
    assert cliente.get(f"/api/videos/{vid}/subtitulos.vtt", headers=docente).status_code == 200
    assert cliente.get(f"/api/videos/{vid}/subtitulos.vtt", headers=estudiante).status_code == 404
    assert cliente.get(f"/api/videos/{vid}/transcripcion.txt", headers=estudiante).status_code == 404
    assert cliente.get(f"/api/videos/{vid}/subtitulos.vtt").status_code in (401, 403)
    assert cliente.get("/api/videos/9999/subtitulos.vtt", headers=docente).status_code == 404


# ---------- Limpieza de datos ----------

def test_eliminar_cuestionario_borra_conversaciones_del_tutor(cliente, docente, estudiante, cuestionario, ia_generica, sesion_factory):
    responde_tutor(ia_generica)
    preguntar(cliente, estudiante, cuestionario)
    assert cliente.delete(f"/api/cuestionarios/{cuestionario}", headers=docente).status_code == 204
    with sesion_factory() as db:
        assert db.scalars(select(MensajeTutor)).first() is None


def test_eliminar_cuenta_borra_tutor_y_banco(cliente, docente, cuestionario, ia_generica, sesion_factory):
    responde_tutor(ia_generica)
    preguntar(cliente, docente, cuestionario)
    guardar_banco(cliente, docente, cuestionario)
    r = cliente.request("DELETE", "/api/auth/cuenta", json={"password": PASSWORD}, headers=docente)
    assert r.status_code == 204
    with sesion_factory() as db:
        assert db.scalars(select(MensajeTutor)).first() is None
        assert db.scalars(select(Pregunta)).first() is None
