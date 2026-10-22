"""Pruebas del Sprint 7: clase en vivo (HTTP + WebSocket), puntaje, permisos, historial/CSV y notificaciones."""
import json
import time
from contextlib import asynccontextmanager
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app import main
from app.modelos import (
    Cuestionario,
    Matricula,
    Notificacion,
    ParticipanteVivo,
    Repaso,
    RespuestaVivo,
    SesionVivo,
    ahora,
)
from app.services import vivo as sv
from tests.conftest import _registrar
from tests.test_sprint6 import _unir, admin, estructura, grupo  # noqa: F401  (fixtures reutilizadas)


@pytest.fixture()
def cv(cliente, monkeypatch):
    """Cliente con un único bucle de eventos (necesario para el temporizador y la difusión por WebSocket)."""

    @asynccontextmanager
    async def sin_lifespan(_):
        yield

    monkeypatch.setattr(main.app.router, "lifespan_context", sin_lifespan)
    with TestClient(main.app) as c:
        yield c


def _jwt(headers: dict) -> str:
    return headers["Authorization"].split()[1]


@pytest.fixture()
def cid(docente, crear_cuestionario):
    return crear_cuestionario(docente)  # sin publicar: la clase en vivo funciona con cualquier estado


@pytest.fixture()
def sesion(cv, docente, cid):
    r = cv.post(f"/api/cuestionarios/{cid}/vivo", json={"segundos_por_pregunta": 20}, headers=docente)
    assert r.status_code == 201, r.text
    return r.json()


def _unir_vivo(cv, pin: str, apodo: str, headers: dict | None = None):
    return cv.post("/api/vivo/unirse", json={"pin": pin, "apodo": apodo}, headers=headers or {})


def _hasta(ws, estado: str, max_msgs: int = 12) -> dict:
    for _ in range(max_msgs):
        msg = ws.receive_json()
        if msg.get("estado") == estado:
            return msg
    raise AssertionError(f"No llegó el estado {estado}")


# ---------- Puntaje y apodos (unitarias) ----------

def test_puntaje_estilo_kahoot_por_tiempo():
    assert sv.calcular_puntos(True, 0, 30) == 1000
    assert sv.calcular_puntos(True, 15000, 30) == 750
    assert sv.calcular_puntos(True, 30000, 30) == 500
    assert sv.calcular_puntos(True, 99999, 30) == 500  # fuera de tiempo no baja de la base
    assert sv.calcular_puntos(False, 0, 30) == 0
    assert sv.calcular_puntos(None, 0, 30) == 0  # abierta: no puntúa


@pytest.mark.parametrize("apodo", ["Puta", "p u t 4", "M1erda", "HIJUEPUTA99", "fuck_you", "Nazi", "culo"])
def test_filtro_ofensivo_rechaza(apodo):
    assert sv.es_ofensivo(apodo)


@pytest.mark.parametrize("apodo", ["Penélope", "Ana", "Compañero", "Grupo 3", "Asia", "Sebastián"])
def test_filtro_ofensivo_no_da_falsos_positivos(apodo):
    assert not sv.es_ofensivo(apodo)


# ---------- Crear y unirse ----------

def test_docente_crea_sesion_con_pin_de_6_digitos(sesion):
    assert len(sesion["pin"]) == 6 and sesion["pin"].isdigit()
    assert sesion["estado"] == "lobby" and sesion["segundos_por_pregunta"] == 20 and sesion["total_preguntas"] == 3


def test_segundos_fuera_de_rango_se_rechazan(cv, docente, cid):
    for s in (9, 121):
        assert cv.post(f"/api/cuestionarios/{cid}/vivo", json={"segundos_por_pregunta": s}, headers=docente).status_code == 422
    assert cv.post(f"/api/cuestionarios/{cid}/vivo", headers=docente).json()["segundos_por_pregunta"] == 30  # por defecto


def test_pines_unicos_entre_sesiones_activas(cv, docente, cid):
    pines = {cv.post(f"/api/cuestionarios/{cid}/vivo", headers=docente).json()["pin"] for _ in range(15)}
    assert len(pines) == 15


def test_solo_el_docente_dueno_crea_sesion(cv, cid, estudiante):
    assert cv.post(f"/api/cuestionarios/{cid}/vivo", headers=estudiante).status_code == 403
    otro = _registrar(cv, "docente", "Otro Docente", "otro@prueba.com")
    assert cv.post(f"/api/cuestionarios/{cid}/vivo", headers=otro).status_code == 403
    assert cv.post("/api/cuestionarios/9999/vivo", headers=otro).status_code == 404
    assert cv.post(f"/api/cuestionarios/{cid}/vivo").status_code == 401


def test_unirse_sin_cuenta_devuelve_token(cv, sesion):
    r = _unir_vivo(cv, sesion["pin"], "  Ana   Lu  ")
    assert r.status_code == 200
    assert r.json()["apodo"] == "Ana Lu" and len(r.json()["token"]) >= 20


def test_unirse_pin_inexistente_o_mal_formado(cv, sesion):
    assert _unir_vivo(cv, "000000", "Ana").status_code == 404
    assert _unir_vivo(cv, "12ab56", "Ana").status_code == 422


def test_apodo_duplicado_ofensivo_y_longitud(cv, sesion):
    pin = sesion["pin"]
    assert _unir_vivo(cv, pin, "Ana").status_code == 200
    assert _unir_vivo(cv, pin, "ana").status_code == 409  # sin distinguir mayúsculas
    assert _unir_vivo(cv, pin, "Puta").status_code == 422
    assert _unir_vivo(cv, pin, "A").status_code == 422
    assert _unir_vivo(cv, pin, "x" * 21).status_code == 422


def test_unirse_con_cuenta_vincula_y_reconecta(cv, sesion, estudiante, sesion_factory):
    pin = sesion["pin"]
    a = _unir_vivo(cv, pin, "Estu", estudiante).json()
    b = _unir_vivo(cv, pin, "Otro nombre", estudiante).json()  # mismo usuario: recupera su lugar
    assert a["token"] == b["token"] and b["apodo"] == "Estu"
    with sesion_factory() as db:
        assert db.query(ParticipanteVivo).one().usuario_id is not None


def test_maximo_200_participantes(cv, sesion, monkeypatch):
    monkeypatch.setattr(sv, "MAX_PARTICIPANTES", 2)
    assert _unir_vivo(cv, sesion["pin"], "Uno").status_code == 200
    assert _unir_vivo(cv, sesion["pin"], "Dos").status_code == 200
    r = _unir_vivo(cv, sesion["pin"], "Tres")
    assert r.status_code == 409 and "llena" in r.json()["detail"]
    assert sv.MAX_PARTICIPANTES == 2


# ---------- No filtrar la respuesta correcta ----------

def test_sondeo_http_no_filtra_respuesta_correcta_antes_del_cierre(cv, docente, sesion):
    pin, sid = sesion["pin"], sesion["id"]
    tok = _unir_vivo(cv, pin, "Ana").json()["token"]
    assert cv.post(f"/api/vivo/sesiones/{sid}/accion", json={"accion": "iniciar"}, headers=docente).status_code == 204
    for snap in (cv.get(f"/api/vivo/{pin}/estado", params={"participante": tok}).json(),
                 cv.get(f"/api/vivo/{pin}/estado", headers=docente).json()):
        assert snap["estado"] == "pregunta" and snap["resultados"] is None
        assert "correcta" not in snap["pregunta"] and "respuesta_correcta" not in snap["pregunta"]
        texto = json.dumps(snap)
        assert "Porque sí" not in texto  # tampoco la explicación
    # Sin credenciales solo se ve información mínima
    publico = cv.get(f"/api/vivo/{pin}/estado").json()
    assert publico["rol"] == "publico" and "pregunta" not in publico
    # Responder y cerrar revela la correcta
    assert cv.post(f"/api/vivo/{pin}/responder", json={"token": tok, "respuesta": "A"}).status_code == 204  # todos respondieron: cierra
    snap = cv.get(f"/api/vivo/{pin}/estado", params={"participante": tok}).json()
    assert snap["estado"] == "resultados_pregunta" and snap["resultados"]["correcta"] == "B"
    assert snap["yo"]["correcta"] is False and snap["yo"]["puntos_ganados"] == 0


def test_participante_no_reconocido_en_sondeo(cv, sesion):
    assert cv.get(f"/api/vivo/{sesion['pin']}/estado", params={"participante": "x" * 30}).status_code == 403
    assert cv.get("/api/vivo/111111/estado").status_code == 404


# ---------- Flujo completo por WebSocket ----------

def test_flujo_websocket_completo(cv, docente, sesion, sesion_factory, estudiante):
    pin, sid = sesion["pin"], sesion["id"]
    ta = _unir_vivo(cv, pin, "Ana", estudiante).json()["token"]  # con cuenta
    tb = _unir_vivo(cv, pin, "Beto").json()["token"]
    with cv.websocket_connect(f"/ws/vivo/{pin}?token={_jwt(docente)}") as pres, \
            cv.websocket_connect(f"/ws/vivo/{pin}?participante={ta}") as wa, \
            cv.websocket_connect(f"/ws/vivo/{pin}?participante={tb}") as wb:
        lobby = pres.receive_json()
        assert lobby["estado"] == "lobby" and lobby["rol"] == "presentador"
        assert lobby["participantes"] == ["Ana", "Beto"] and lobby["num_participantes"] == 2
        assert wa.receive_json()["yo"]["apodo"] == "Ana"
        wb.receive_json()

        # Pregunta 1 (opción múltiple, correcta B)
        pres.send_json({"accion": "iniciar"})
        p = _hasta(pres, "pregunta")
        assert p["indice"] == 0 and p["pregunta"]["tipo"] == "opcion_multiple" and p["restante_ms"] > 15000
        assert "correcta" not in p["pregunta"] and p["resultados"] is None
        qa, qb = _hasta(wa, "pregunta"), _hasta(wb, "pregunta")
        assert "respuesta_correcta" not in json.dumps(qa)

        wa.send_json({"accion": "responder", "respuesta": "B"})
        conf = wa.receive_json()
        assert conf["yo"]["respondio"] is True and conf["yo"]["correcta"] is None  # aún sin revelar
        cuenta = pres.receive_json()
        assert cuenta["respondieron"] == 1 and cuenta["estado"] == "pregunta"

        wb.send_json({"accion": "responder", "respuesta": "A"})
        res = _hasta(pres, "resultados_pregunta")  # todos respondieron: cierre automático
        assert res["resultados"]["correcta"] == "B"
        dist = {d["opcion"]: d["cantidad"] for d in res["resultados"]["distribucion"]}
        assert dist == {"A": 1, "B": 1, "C": 0, "D": 0}
        assert [d["correcta"] for d in res["resultados"]["distribucion"]] == [False, True, False, False]
        assert res["ranking"][0]["apodo"] == "Ana" and 900 <= res["ranking"][0]["puntos"] <= 1000
        ra = _hasta(wa, "resultados_pregunta")
        assert ra["yo"]["correcta"] is True and ra["yo"]["posicion"] == 1 and ra["yo"]["puntos_ganados"] >= 900
        rb = _hasta(wb, "resultados_pregunta")
        assert rb["yo"]["correcta"] is False and rb["yo"]["puntos_ganados"] == 0 and rb["yo"]["posicion"] == 2

        # Responder fuera de pregunta o dos veces da error sin romper la conexión
        wb.send_json({"accion": "responder", "respuesta": "B"})
        assert wb.receive_json()["tipo"] == "error"

        # Pregunta 2 (V/F): el presentador la cierra con «saltar» antes de que todos respondan
        pres.send_json({"accion": "siguiente"})
        assert _hasta(pres, "pregunta")["indice"] == 1
        _hasta(wa, "pregunta"), _hasta(wb, "pregunta")
        wa.send_json({"accion": "responder", "respuesta": "Verdadero"})  # Beto no responde
        assert pres.receive_json()["respondieron"] == 1
        pres.send_json({"accion": "saltar"})
        r2 = _hasta(pres, "resultados_pregunta")
        assert r2["resultados"]["correcta"] == "Verdadero" and r2["resultados"]["respondieron"] == 1

        # Pregunta 3 (abierta): se responde pero no puntúa y el presentador ve el texto
        pres.send_json({"accion": "siguiente"})
        _hasta(pres, "pregunta"), _hasta(wa, "pregunta"), _hasta(wb, "pregunta")
        wa.send_json({"accion": "responder", "respuesta": "La idea es X"})
        wb.send_json({"accion": "responder", "respuesta": "No sé"})
        r3 = _hasta(pres, "resultados_pregunta")
        assert sorted(r3["resultados"]["abiertas"]) == ["La idea es X", "No sé"] and r3["resultados"]["correcta"] is None
        assert _hasta(wa, "resultados_pregunta")["resultados"]["abiertas"] == []  # los participantes no ven las demás

        # Fin: podio
        pres.send_json({"accion": "siguiente"})
        fin = _hasta(pres, "finalizada")
        assert [x["apodo"] for x in fin["ranking"]] == ["Ana", "Beto"]
        assert fin["ranking"][0]["puntos"] > fin["ranking"][1]["puntos"] == 0
        assert _hasta(wb, "finalizada")["yo"]["posicion"] == 2

    with sesion_factory() as db:
        s = db.get(SesionVivo, sid)
        assert s.estado == "finalizada" and s.finalizada_en is not None
        assert db.query(RespuestaVivo).count() == 5
        abiertas = db.query(RespuestaVivo).filter(RespuestaVivo.correcta.is_(None)).count()
        assert abiertas == 2
        assert {p.apodo: p.puntaje for p in db.query(ParticipanteVivo)}["Ana"] > 1800
        # El participante con cuenta recibe su resultado; el anónimo no
        notis = db.query(Notificacion).all()
        assert len(notis) == 1 and notis[0].tipo == "clase_vivo" and "puesto 1" in notis[0].mensaje
    # Una sesión finalizada ya no admite más participantes
    assert _unir_vivo(cv, pin, "Tarde").status_code == 410


def test_temporizador_del_servidor_cierra_la_pregunta(cv, docente, sesion, monkeypatch):
    """El servidor (no el cliente) cierra la pregunta al agotarse el tiempo."""
    pin = sesion["pin"]
    ta = _unir_vivo(cv, pin, "Ana").json()["token"]
    _unir_vivo(cv, pin, "Beto")
    m = sv.obtener(pin)
    m.segundos = 1  # acelera el temporizador (el mínimo de la API es 10 s)
    with cv.websocket_connect(f"/ws/vivo/{pin}?token={_jwt(docente)}") as pres, \
            cv.websocket_connect(f"/ws/vivo/{pin}?participante={ta}") as wa:
        pres.receive_json(), wa.receive_json()
        pres.send_json({"accion": "iniciar"})
        _hasta(pres, "pregunta")
        wa.send_json({"accion": "responder", "respuesta": "B"})  # Beto no responde: el cierre llega por tiempo
        t0 = time.time()
        res = _hasta(pres, "resultados_pregunta")
        assert time.time() - t0 < 4 and res["resultados"]["respondieron"] == 1


def test_reconexion_con_token_recupera_el_estado(cv, docente, sesion):
    pin = sesion["pin"]
    ta = _unir_vivo(cv, pin, "Ana").json()["token"]
    _unir_vivo(cv, pin, "Beto")
    with cv.websocket_connect(f"/ws/vivo/{pin}?participante={ta}") as wa:
        wa.receive_json()
        cv.post(f"/api/vivo/sesiones/{sesion['id']}/accion", json={"accion": "iniciar"}, headers=docente)
        _hasta(wa, "pregunta")
        wa.send_json({"accion": "responder", "respuesta": "B"})
        assert wa.receive_json()["yo"]["respondio"] is True
    # Se cae la conexión y vuelve con el mismo token: ve la pregunta en curso y que ya respondió
    with cv.websocket_connect(f"/ws/vivo/{pin}?participante={ta}") as wa2:
        snap = wa2.receive_json()
        assert snap["estado"] == "pregunta" and snap["yo"]["apodo"] == "Ana"
        assert snap["yo"]["respondio"] is True and snap["yo"]["mi_respuesta"] == "B"
        assert snap["restante_ms"] > 0 and "correcta" not in snap["pregunta"]


def test_sesion_se_reconstruye_desde_la_bd_tras_reinicio(cv, docente, sesion):
    pin = sesion["pin"]
    ta = _unir_vivo(cv, pin, "Ana").json()["token"]
    _unir_vivo(cv, pin, "Beto")
    cv.post(f"/api/vivo/sesiones/{sesion['id']}/accion", json={"accion": "iniciar"}, headers=docente)
    cv.post(f"/api/vivo/{pin}/responder", json={"token": ta, "respuesta": "B"})
    sv._sesiones.clear()  # simula el reinicio del servidor
    snap = cv.get(f"/api/vivo/{pin}/estado", params={"participante": ta}).json()
    assert snap["estado"] == "pregunta" and snap["yo"]["respondio"] is True and snap["yo"]["puntos"] >= 900


# ---------- Permisos del WebSocket y de los controles ----------

def test_websocket_rechaza_credenciales_invalidas(cv, docente, estudiante, sesion):
    pin = sesion["pin"]
    for url, codigo in (
        (f"/ws/vivo/{pin}?token={_jwt(estudiante)}", 4403),  # JWT de alguien que no es el dueño
        (f"/ws/vivo/{pin}?token=basura", 4403),
        (f"/ws/vivo/{pin}?participante={'z' * 30}", 4401),
        (f"/ws/vivo/{pin}", 4401),
        ("/ws/vivo/999999?token=" + _jwt(docente), 4404),
    ):
        with pytest.raises(WebSocketDisconnect) as e:
            with cv.websocket_connect(url):
                pass
        assert e.value.code == codigo


def test_un_participante_no_puede_controlar_la_sesion(cv, sesion):
    pin = sesion["pin"]
    ta = _unir_vivo(cv, pin, "Ana").json()["token"]
    with cv.websocket_connect(f"/ws/vivo/{pin}?participante={ta}") as wa:
        wa.receive_json()
        wa.send_json({"accion": "iniciar"})
        assert wa.receive_json()["tipo"] == "error"
    assert sv.obtener(pin).estado == "lobby"


def test_controles_http_solo_para_el_dueno(cv, docente, estudiante, sesion):
    sid = sesion["id"]
    otro = _registrar(cv, "docente", "Otro Docente", "otro@prueba.com")
    for h in (estudiante, otro):
        assert cv.post(f"/api/vivo/sesiones/{sid}/accion", json={"accion": "iniciar"}, headers=h).status_code == 403
        assert cv.get(f"/api/vivo/sesiones/{sid}", headers=h).status_code == 403
    assert cv.post(f"/api/vivo/sesiones/{sid}/accion", json={"accion": "explotar"}, headers=docente).status_code == 422
    assert cv.get(f"/api/vivo/sesiones/{sid}", headers=docente).json()["pin"] == sesion["pin"]
    # Acción repetida / fuera de orden
    cv.post(f"/api/vivo/sesiones/{sid}/accion", json={"accion": "iniciar"}, headers=docente)
    assert cv.post(f"/api/vivo/sesiones/{sid}/accion", json={"accion": "iniciar"}, headers=docente).status_code == 409


def test_respuesta_invalida_y_doble_respuesta(cv, docente, sesion):
    pin = sesion["pin"]
    ta = _unir_vivo(cv, pin, "Ana").json()["token"]
    _unir_vivo(cv, pin, "Beto")
    assert cv.post(f"/api/vivo/{pin}/responder", json={"token": ta, "respuesta": "B"}).status_code == 409  # sin pregunta abierta
    cv.post(f"/api/vivo/sesiones/{sesion['id']}/accion", json={"accion": "iniciar"}, headers=docente)
    assert cv.post(f"/api/vivo/{pin}/responder", json={"token": ta, "respuesta": "Z"}).status_code == 422  # opción inexistente
    assert cv.post(f"/api/vivo/{pin}/responder", json={"token": ta, "respuesta": "B"}).status_code == 204
    assert cv.post(f"/api/vivo/{pin}/responder", json={"token": ta, "respuesta": "A"}).status_code == 409  # solo una vez
    assert cv.post(f"/api/vivo/{pin}/responder", json={"token": "x" * 30, "respuesta": "A"}).status_code == 403


def test_sesion_abandonada_se_cierra_tras_2_horas(cv, sesion, sesion_factory):
    pin = sesion["pin"]
    sv.obtener(pin).actividad -= 3 * 3600
    assert cv.get(f"/api/vivo/{pin}/estado").json()["estado"] == "finalizada"
    with sesion_factory() as db:
        assert db.get(SesionVivo, sesion["id"]).estado == "finalizada"
    # El PIN de una sesión finalizada se puede reutilizar y, en la BD, también expira lo que no está en memoria
    sv._sesiones.clear()
    with sesion_factory() as db:
        s = SesionVivo(cuestionario_id=1, docente_id=1, pin="123456", actividad_en=ahora() - timedelta(hours=3))
        db.add(s)
        db.commit()
    assert cv.get("/api/vivo/123456/estado").status_code == 404
    with sesion_factory() as db:
        assert db.query(SesionVivo).filter_by(pin="123456").one().estado == "finalizada"


# ---------- Historial y CSV ----------

def _jugar_una_pregunta(cv, docente, sesion, nombres_respuestas: dict[str, str]):
    pin = sesion["pin"]
    for apodo in nombres_respuestas:
        _unir_vivo(cv, pin, apodo)
    cv.post(f"/api/vivo/sesiones/{sesion['id']}/accion", json={"accion": "iniciar"}, headers=docente)
    m = sv.obtener(pin)
    for pid, apodo in m.apodos.items():
        tok = next(t for t, i in m.tokens.items() if i == pid)
        cv.post(f"/api/vivo/{pin}/responder", json={"token": tok, "respuesta": nombres_respuestas[apodo]})
    cv.post(f"/api/vivo/sesiones/{sesion['id']}/accion", json={"accion": "finalizar"}, headers=docente)


def test_historial_con_porcentaje_de_acierto(cv, docente, cid, sesion):
    _jugar_una_pregunta(cv, docente, sesion, {"Ana": "B", "Beto": "A", "Caro": "B", "Dani": "B"})
    h = cv.get(f"/api/cuestionarios/{cid}/vivo", headers=docente).json()
    assert len(h) == 1 and h[0]["participantes"] == 4 and h[0]["estado"] == "finalizada"
    assert h[0]["promedio_acierto"] == 75.0
    assert h[0]["preguntas"][0]["porcentaje_acierto"] == 75.0 and h[0]["preguntas"][0]["respuestas"] == 4
    assert h[0]["preguntas"][1]["porcentaje_acierto"] is None and h[0]["preguntas"][1]["respuestas"] == 0


def test_historial_solo_para_el_dueno(cv, docente, cid, estudiante):
    assert cv.get(f"/api/cuestionarios/{cid}/vivo", headers=estudiante).status_code == 403
    otro = _registrar(cv, "docente", "Otro Docente", "otro@prueba.com")
    assert cv.get(f"/api/cuestionarios/{cid}/vivo", headers=otro).status_code == 403
    assert cv.get(f"/api/cuestionarios/{cid}/vivo.csv", headers=otro).status_code == 403
    assert cv.get(f"/api/cuestionarios/{cid}/vivo", headers=docente).json() == []


def test_csv_con_bom_y_proteccion_de_formulas(cv, docente, cid, sesion):
    _jugar_una_pregunta(cv, docente, sesion, {"=CMD()": "B", "Beto": "A"})
    r = cv.get(f"/api/cuestionarios/{cid}/vivo.csv", headers=docente)
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
    assert r.content.startswith("﻿".encode("utf-8"))
    texto = r.content.decode("utf-8-sig")
    assert "Participantes" in texto and "'=CMD()" in texto and "\n=CMD" not in texto and ",=CMD" not in texto
    assert "Beto" in texto


def test_borrar_cuestionario_borra_sus_sesiones_en_vivo(cv, docente, cid, sesion, sesion_factory):
    _jugar_una_pregunta(cv, docente, sesion, {"Ana": "B"})
    assert cv.delete(f"/api/cuestionarios/{cid}", headers=docente).status_code == 204
    with sesion_factory() as db:
        assert db.query(SesionVivo).count() == db.query(ParticipanteVivo).count() == db.query(RespuestaVivo).count() == 0


# ---------- Notificaciones ----------

def _notis(cliente, headers, **params):
    r = cliente.get("/api/notificaciones", params=params, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_notificaciones_requieren_sesion(cliente):
    assert cliente.get("/api/notificaciones").status_code == 401
    assert cliente.get("/api/notificaciones/no-leidas").status_code == 401


def test_publicar_en_grupo_notifica_a_matriculados_una_sola_vez(cliente, docente, estudiante, otro_estudiante, grupo, crear_cuestionario):
    _unir(cliente, estudiante, grupo)  # otro_estudiante no está matriculado
    cid = crear_cuestionario(docente)
    assert _notis(cliente, estudiante)["total"] == 0
    assert cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True, "grupo_id": grupo["id"]}, headers=docente).status_code == 200
    n = _notis(cliente, estudiante)
    assert n["total"] == 1 and n["no_leidas"] == 1
    assert n["items"][0]["tipo"] == "publicado" and n["items"][0]["enlace"] == f"/cuestionarios/{cid}"
    assert _notis(cliente, otro_estudiante)["total"] == 0
    # Despublicar y publicar de nuevo no duplica
    cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": False}, headers=docente)
    cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True}, headers=docente)
    assert _notis(cliente, estudiante)["total"] == 1
    # Publicar sin grupo no notifica a nadie
    otro = crear_cuestionario(docente, "https://www.youtube.com/watch?v=aaaaaaaaaaa")
    cliente.post(f"/api/cuestionarios/{otro}/publicar", json={"publicado": True}, headers=docente)
    assert _notis(cliente, estudiante)["total"] == 1


def test_contador_y_marcado_de_lectura(cliente, docente, estudiante, grupo, crear_cuestionario):
    _unir(cliente, estudiante, grupo)
    for url in ("https://www.youtube.com/watch?v=aaaaaaaaaaa", "https://www.youtube.com/watch?v=bbbbbbbbbbb"):
        cid = crear_cuestionario(docente, url)
        cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True, "grupo_id": grupo["id"]}, headers=docente)
    assert cliente.get("/api/notificaciones/no-leidas", headers=estudiante).json() == {"no_leidas": 2}
    items = _notis(cliente, estudiante)["items"]
    assert cliente.post(f"/api/notificaciones/{items[0]['id']}/leer", headers=estudiante).json() == {"no_leidas": 1}
    assert [i["leida"] for i in _notis(cliente, estudiante)["items"]] == [True, False]
    assert len(_notis(cliente, estudiante, solo_no_leidas=True)["items"]) == 1
    assert cliente.post("/api/notificaciones/leer-todas", headers=estudiante).json() == {"no_leidas": 0}
    assert cliente.get("/api/notificaciones/no-leidas", headers=estudiante).json() == {"no_leidas": 0}


def test_notificaciones_paginadas_y_privadas(cliente, docente, estudiante, otro_estudiante, grupo, crear_cuestionario, sesion_factory):
    _unir(cliente, estudiante, grupo)
    with sesion_factory() as db:
        uid = db.query(Matricula).one().estudiante_id
        for i in range(25):
            db.add(Notificacion(usuario_id=uid, tipo="publicado", titulo=f"N{i}", creada_en=ahora() - timedelta(minutes=i)))
        db.commit()
    p1 = _notis(cliente, estudiante, pagina=1, por_pagina=10)
    p3 = _notis(cliente, estudiante, pagina=3, por_pagina=10)
    assert p1["total"] == 25 and len(p1["items"]) == 10 and len(p3["items"]) == 5
    assert p1["items"][0]["titulo"] == "N0"  # la más reciente primero
    assert cliente.get("/api/notificaciones", params={"por_pagina": 500}, headers=estudiante).status_code == 422
    # Nadie lee ni marca las de otro
    nid = p1["items"][0]["id"]
    assert cliente.post(f"/api/notificaciones/{nid}/leer", headers=otro_estudiante).status_code == 404
    assert _notis(cliente, otro_estudiante)["total"] == 0


def test_repaso_vencido_genera_notificacion_una_vez(cliente, docente, estudiante, crear_cuestionario, sesion_factory):
    cid = crear_cuestionario(docente)
    cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True}, headers=docente)
    cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante)
    with sesion_factory() as db:
        from app.modelos import Usuario
        uid = db.query(Usuario).filter_by(email="estudiante@prueba.com").one().id
        db.add(Repaso(usuario_id=uid, cuestionario_id=cid, disponible_desde=ahora() + timedelta(days=3)))
        db.commit()
    assert _notis(cliente, estudiante)["total"] == 0  # aún no vence
    with sesion_factory() as db:
        db.query(Repaso).update({"disponible_desde": ahora() - timedelta(hours=1)})
        db.commit()
    n = _notis(cliente, estudiante)
    assert n["total"] == 1 and n["items"][0]["tipo"] == "repaso"
    assert _notis(cliente, estudiante)["total"] == 1  # no se vuelve a notificar
    # Un repaso completado no notifica
    with sesion_factory() as db:
        db.query(Notificacion).delete()
        db.query(Repaso).update({"completado_intento_id": 1})
        db.commit()
    assert _notis(cliente, estudiante)["total"] == 0


def test_alerta_temprana_notifica_al_docente_del_grupo(cliente, docente, estudiante, otro_estudiante, grupo, sesion_factory):
    _unir(cliente, estudiante, grupo)
    with sesion_factory() as db:
        db.query(Matricula).update({"creado_en": ahora() - timedelta(days=20)})
        db.commit()
    n = _notis(cliente, docente)
    assert n["total"] == 1 and n["items"][0]["tipo"] == "alerta" and "Estudiante Uno" in n["items"][0]["titulo"]
    from app.services import notificaciones as ns
    ns._ultimo_calculo_alertas.clear()
    assert _notis(cliente, docente)["total"] == 1  # misma alerta: sin duplicado
    assert _notis(cliente, estudiante)["total"] == 0  # el estudiante no recibe alertas


def test_resultado_de_clase_en_vivo_llega_a_notificaciones(cv, docente, estudiante, sesion):
    pin = sesion["pin"]
    _unir_vivo(cv, pin, "Estu", estudiante)
    _unir_vivo(cv, pin, "Anon")
    cv.post(f"/api/vivo/sesiones/{sesion['id']}/accion", json={"accion": "finalizar"}, headers=docente)
    n = _notis(cv, estudiante)
    assert n["total"] == 1 and n["items"][0]["tipo"] == "clase_vivo" and "puesto" in n["items"][0]["mensaje"]


def test_eliminar_cuenta_limpia_notificaciones_y_participaciones(cv, docente, estudiante, sesion, sesion_factory):
    _unir_vivo(cv, sesion["pin"], "Estu", estudiante)
    cv.post(f"/api/vivo/sesiones/{sesion['id']}/accion", json={"accion": "finalizar"}, headers=docente)
    r = cv.request("DELETE", "/api/auth/cuenta", json={"password": "Clave12345"}, headers=estudiante)
    assert r.status_code == 204, r.text
    with sesion_factory() as db:
        assert db.query(Notificacion).count() == 0
        assert db.query(ParticipanteVivo).one().usuario_id is None  # la participación queda anónima
