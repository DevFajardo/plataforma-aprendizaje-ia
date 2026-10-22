"""Pruebas del Sprint 6: estructura académica, roles, cursos, RA, panel de coordinación, alertas y PDF."""
from datetime import timedelta

import pytest
from sqlalchemy import create_engine, text

from app import db as modulo_db
from app.modelos import AlertaSeguimiento, Cuestionario, Grupo, Intento, Matricula, Pregunta, Repaso, Usuario, ahora
from app.schemas import Pregunta as PreguntaIA
from app.services.ia.base import construir_prompt
from app.services.logro import semaforo
from tests.conftest import PASSWORD, _registrar


# ---------- Fábricas ----------

def _con_rol(cliente, sesion_factory, rol: str, nombre: str, email: str, programa_id: int | None = None) -> dict:
    """Las cuentas coordinador/admin no se crean por el registro público: se promueven en la BD."""
    headers = _registrar(cliente, "estudiante", nombre, email)
    with sesion_factory() as db:
        u = db.query(Usuario).filter_by(email=email).one()
        u.rol, u.programa_id = rol, programa_id
        db.commit()
    return headers


@pytest.fixture()
def admin(cliente, sesion_factory):
    return _con_rol(cliente, sesion_factory, "admin", "Admin Uno", "admin@prueba.com")


@pytest.fixture()
def tercer_estudiante(cliente):
    return _registrar(cliente, "estudiante", "Estudiante Tres", "estudiante3@prueba.com")


@pytest.fixture()
def estructura(cliente, admin):
    """Facultad > 2 programas. Programa 1: asignatura con RA1 y RA2 (RA3 sin asignar). Programa 2: otra asignatura con su RA."""
    def post(ruta, cuerpo):
        r = cliente.post(ruta, json=cuerpo, headers=admin)
        assert r.status_code == 201, r.text
        return r.json()

    fac = post("/api/admin/facultades", {"nombre": "Facultad de Ingeniería"})
    p1 = post("/api/admin/programas", {"facultad_id": fac["id"], "nombre": "Ingeniería de Sistemas", "codigo": "IS"})
    p2 = post("/api/admin/programas", {"facultad_id": fac["id"], "nombre": "Administración", "codigo": "AD"})
    a1 = post("/api/admin/asignaturas", {"programa_id": p1["id"], "nombre": "Bases de Datos", "codigo": "BD1", "semestre": 4})
    a2 = post("/api/admin/asignaturas", {"programa_id": p2["id"], "nombre": "Contabilidad", "codigo": "CO1", "semestre": 2})
    ra1 = post("/api/admin/ras", {"programa_id": p1["id"], "codigo": "ra1", "descripcion": "Diseña modelos de datos"})
    ra2 = post("/api/admin/ras", {"programa_id": p1["id"], "codigo": "RA2", "descripcion": "Consulta bases de datos con SQL"})
    ra3 = post("/api/admin/ras", {"programa_id": p1["id"], "codigo": "RA3", "descripcion": "RA sin asignar a la asignatura"})
    ra_otro = post("/api/admin/ras", {"programa_id": p2["id"], "codigo": "RA1", "descripcion": "RA de otro programa"})
    r = cliente.put(f"/api/admin/asignaturas/{a1['id']}/ras", json={"ra_ids": [ra1["id"], ra2["id"]]}, headers=admin)
    assert r.status_code == 200, r.text
    cliente.put(f"/api/admin/asignaturas/{a2['id']}/ras", json={"ra_ids": [ra_otro["id"]]}, headers=admin)
    return {"fac": fac, "p1": p1, "p2": p2, "a1": a1, "a2": a2, "ra1": ra1, "ra2": ra2, "ra3": ra3, "ra_otro": ra_otro}


@pytest.fixture()
def coordinador(cliente, sesion_factory, estructura):
    return _con_rol(cliente, sesion_factory, "coordinador", "Coordinador Uno", "coord@prueba.com", estructura["p1"]["id"])


@pytest.fixture()
def grupo(cliente, docente, estructura):
    r = cliente.post("/api/grupos", json={"asignatura_id": estructura["a1"]["id"], "periodo": "2026-2", "nombre": "Grupo A"}, headers=docente)
    assert r.status_code == 201, r.text
    return r.json()


def _unir(cliente, headers, grupo):
    r = cliente.post("/api/mis-cursos/unirse", json={"codigo": grupo["codigo_ingreso"]}, headers=headers)
    assert r.status_code == 200, r.text


@pytest.fixture()
def cuestionario_curso(cliente, docente, grupo, estructura, crear_cuestionario):
    """Cuestionario publicado en el grupo; pregunta 1 (opción múltiple) -> RA1 y pregunta 2 (V/F) -> RA2."""
    cid = crear_cuestionario(docente)
    assert cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True, "grupo_id": grupo["id"]}, headers=docente).status_code == 200
    c = cliente.get(f"/api/cuestionarios/{cid}", headers=docente).json()
    for p, ra, bloom in zip(c["preguntas"][:2], (estructura["ra1"]["id"], estructura["ra2"]["id"]), ("recordar", "aplicar")):
        cuerpo = {"tipo": p["tipo"], "enunciado": p["enunciado"], "opciones": p["opciones"], "respuesta_correcta": p["respuesta_correcta"],
                  "explicacion": p["explicacion"], "marca_tiempo": p["marca_tiempo"], "ra_id": ra, "nivel_bloom": bloom}
        r = cliente.put(f"/api/preguntas/{p['id']}", json=cuerpo, headers=docente)
        assert r.status_code == 200, r.text
    return cid


# ---------- Roles y permisos ----------

@pytest.mark.parametrize("rol", ["admin", "coordinador", "superusuario"])
def test_registro_publico_no_permite_roles_privilegiados(cliente, rol):
    r = cliente.post("/api/auth/registro", json={"nombre": "X", "email": "x@x.com", "password": PASSWORD, "rol": rol,
                                                "acepta_tratamiento_datos": True})
    assert r.status_code == 422


def test_endpoints_admin_solo_para_admin(cliente, admin, docente, estudiante, coordinador):
    assert cliente.get("/api/admin/facultades", headers=admin).status_code == 200
    for headers in (docente, estudiante, coordinador):
        assert cliente.get("/api/admin/facultades", headers=headers).status_code == 403
        assert cliente.post("/api/admin/facultades", json={"nombre": "Otra"}, headers=headers).status_code == 403
        assert cliente.get("/api/admin/usuarios", headers=headers).status_code == 403
    assert cliente.get("/api/admin/facultades").status_code == 401


def test_panel_coordinacion_solo_coordinador_y_admin(cliente, admin, coordinador, docente, estudiante):
    for headers in (docente, estudiante):
        assert cliente.get("/api/coordinacion/resumen", headers=headers).status_code == 403
        assert cliente.get("/api/coordinacion/reporte-ra.pdf", headers=headers).status_code == 403
    assert cliente.get("/api/coordinacion/resumen", headers=coordinador).status_code == 200
    assert cliente.get("/api/coordinacion/resumen", headers=admin).status_code == 200


def test_alertas_vedadas_a_estudiantes(cliente, estudiante, docente):
    assert cliente.get("/api/alertas", headers=estudiante).status_code == 403
    assert cliente.get("/api/alertas", headers=docente).status_code == 200
    assert cliente.get("/api/grupos", headers=estudiante).status_code == 403


# ---------- CRUD de estructura ----------

def test_crud_de_estructura_y_ras_por_asignatura(cliente, admin, estructura):
    asignaturas = cliente.get("/api/admin/asignaturas", params={"programa_id": estructura["p1"]["id"]}, headers=admin).json()
    assert [a["nombre"] for a in asignaturas] == ["Bases de Datos"]
    assert sorted(asignaturas[0]["ra_ids"]) == sorted([estructura["ra1"]["id"], estructura["ra2"]["id"]])
    # el código del RA se normaliza a mayúsculas
    assert estructura["ra1"]["codigo"] == "RA1"
    r = cliente.patch(f"/api/admin/ras/{estructura['ra3']['id']}", json={"descripcion": "Descripción nueva"}, headers=admin)
    assert r.json()["descripcion"] == "Descripción nueva"
    r = cliente.patch(f"/api/admin/programas/{estructura['p2']['id']}", json={"nombre": "Administración de Empresas"}, headers=admin)
    assert r.json()["nombre"] == "Administración de Empresas"


def test_duplicados_y_restricciones(cliente, admin, estructura):
    assert cliente.post("/api/admin/facultades", json={"nombre": "Facultad de Ingeniería"}, headers=admin).status_code == 409
    assert cliente.post("/api/admin/programas", json={"facultad_id": estructura["fac"]["id"], "nombre": "Otro", "codigo": "is"}, headers=admin).status_code == 409
    assert cliente.post("/api/admin/ras", json={"programa_id": estructura["p1"]["id"], "codigo": "RA1", "descripcion": "Repetido"}, headers=admin).status_code == 409
    # RA de otro programa no se puede asignar a la asignatura
    r = cliente.put(f"/api/admin/asignaturas/{estructura['a1']['id']}/ras", json={"ra_ids": [estructura["ra_otro"]["id"]]}, headers=admin)
    assert r.status_code == 400
    # no se elimina una facultad/programa/asignatura con contenido
    assert cliente.delete(f"/api/admin/facultades/{estructura['fac']['id']}", headers=admin).status_code == 409
    assert cliente.delete(f"/api/admin/programas/{estructura['p1']['id']}", headers=admin).status_code == 409


def test_no_se_elimina_asignatura_con_grupos_y_eliminar_ra_limpia_preguntas(cliente, admin, docente, grupo, estructura, cuestionario_curso, sesion_factory):
    assert cliente.delete(f"/api/admin/asignaturas/{estructura['a1']['id']}", headers=admin).status_code == 409
    assert cliente.delete(f"/api/admin/ras/{estructura['ra1']['id']}", headers=admin).status_code == 204
    with sesion_factory() as db:
        assert db.query(Pregunta).filter(Pregunta.ra_id == estructura["ra1"]["id"]).count() == 0


def test_admin_gestiona_usuarios(cliente, admin, estudiante, estructura, sesion_factory):
    usuarios = cliente.get("/api/admin/usuarios", headers=admin).json()
    est = next(u for u in usuarios if u["email"] == "estudiante@prueba.com")
    r = cliente.patch(f"/api/admin/usuarios/{est['id']}", json={"rol": "coordinador", "programa_id": estructura["p1"]["id"]}, headers=admin)
    assert r.status_code == 200 and r.json()["rol"] == "coordinador" and r.json()["programa"] == "Ingeniería de Sistemas"
    # al dejar de ser coordinador pierde el programa
    r = cliente.patch(f"/api/admin/usuarios/{est['id']}", json={"rol": "docente"}, headers=admin)
    assert r.json()["programa_id"] is None
    assert cliente.patch(f"/api/admin/usuarios/{est['id']}", json={"rol": "coordinador", "programa_id": 9999}, headers=admin).status_code == 404


def test_admin_no_puede_quitarse_su_rol(cliente, admin):
    yo = cliente.get("/api/auth/yo", headers=admin).json()
    assert cliente.patch(f"/api/admin/usuarios/{yo['id']}", json={"rol": "docente"}, headers=admin).status_code == 400


# ---------- Grupos y matrículas ----------

def test_docente_crea_grupo_con_codigo_de_6_caracteres(cliente, grupo, docente):
    assert len(grupo["codigo_ingreso"]) == 6
    assert grupo["asignatura"] == "Bases de Datos" and grupo["num_matriculados"] == 0
    assert [g["id"] for g in cliente.get("/api/grupos", headers=docente).json()] == [grupo["id"]]


def test_periodo_invalido_y_solo_docente_crea_grupos(cliente, docente, estudiante, estructura):
    cuerpo = {"asignatura_id": estructura["a1"]["id"], "periodo": "dos mil", "nombre": "G"}
    assert cliente.post("/api/grupos", json=cuerpo, headers=docente).status_code == 422
    cuerpo["periodo"] = "2026-1"
    assert cliente.post("/api/grupos", json=cuerpo, headers=estudiante).status_code == 403


def test_grupo_ajeno_no_se_edita_ni_se_ve(cliente, grupo, estructura):
    otro = _registrar(cliente, "docente", "Otro Docente", "otro@prueba.com")
    assert cliente.get("/api/grupos", headers=otro).json() == []
    assert cliente.patch(f"/api/grupos/{grupo['id']}", json={"nombre": "Robado"}, headers=otro).status_code == 403
    assert cliente.delete(f"/api/grupos/{grupo['id']}", headers=otro).status_code == 403
    assert cliente.get(f"/api/grupos/{grupo['id']}/matriculados", headers=otro).status_code == 403


def test_estudiante_se_une_con_codigo(cliente, grupo, estudiante, docente):
    r = cliente.post("/api/mis-cursos/unirse", json={"codigo": grupo["codigo_ingreso"].lower()}, headers=estudiante)
    assert r.status_code == 200 and r.json()["grupo_id"] == grupo["id"]
    assert cliente.post("/api/mis-cursos/unirse", json={"codigo": grupo["codigo_ingreso"]}, headers=estudiante).status_code == 409
    assert cliente.post("/api/mis-cursos/unirse", json={"codigo": "ZZZZZZ"}, headers=estudiante).status_code == 404
    assert cliente.post("/api/mis-cursos/unirse", json={"codigo": grupo["codigo_ingreso"]}, headers=docente).status_code == 403
    m = cliente.get(f"/api/grupos/{grupo['id']}/matriculados", headers=docente).json()
    assert [x["email"] for x in m] == ["estudiante@prueba.com"]


def test_docente_quita_matriculado_y_estudiante_puede_salir(cliente, grupo, estudiante, otro_estudiante, docente):
    _unir(cliente, estudiante, grupo)
    _unir(cliente, otro_estudiante, grupo)
    ids = {x["email"]: x["estudiante_id"] for x in cliente.get(f"/api/grupos/{grupo['id']}/matriculados", headers=docente).json()}
    assert cliente.delete(f"/api/grupos/{grupo['id']}/matriculados/{ids['estudiante@prueba.com']}", headers=docente).status_code == 204
    assert cliente.delete(f"/api/mis-cursos/{grupo['id']}", headers=otro_estudiante).status_code == 204
    assert cliente.get(f"/api/grupos/{grupo['id']}/matriculados", headers=docente).json() == []


def test_mis_cursos_muestra_solo_cuestionarios_publicados_sin_codigo(cliente, docente, grupo, estudiante, otro_estudiante, crear_cuestionario):
    borrador = crear_cuestionario(docente)
    publicado = crear_cuestionario(docente)
    cliente.patch(f"/api/cuestionarios/{borrador}", json={"grupo_id": grupo["id"]}, headers=docente)
    cliente.post(f"/api/cuestionarios/{publicado}/publicar", json={"publicado": True, "grupo_id": grupo["id"]}, headers=docente)
    _unir(cliente, estudiante, grupo)
    cursos = cliente.get("/api/mis-cursos", headers=estudiante).json()
    assert len(cursos) == 1 and [c["id"] for c in cursos[0]["cuestionarios"]] == [publicado]
    assert cursos[0]["docente"] == "Docente Uno" and cursos[0]["periodo"] == "2026-2"
    # quien no está matriculado no ve el curso
    assert cliente.get("/api/mis-cursos", headers=otro_estudiante).json() == []
    # y el estudiante puede abrir el cuestionario directamente
    assert cliente.get(f"/api/cuestionarios/{publicado}", headers=estudiante).status_code == 200


def test_cuestionario_solo_se_asigna_a_grupos_propios(cliente, docente, grupo, crear_cuestionario):
    otro = _registrar(cliente, "docente", "Otro Docente", "otro@prueba.com")
    cid = crear_cuestionario(otro)
    assert cliente.patch(f"/api/cuestionarios/{cid}", json={"grupo_id": grupo["id"]}, headers=otro).status_code == 403
    assert cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True, "grupo_id": grupo["id"]}, headers=otro).status_code == 403


def test_eliminar_grupo_desvincula_cuestionarios(cliente, docente, grupo, cuestionario_curso, estudiante):
    _unir(cliente, estudiante, grupo)
    assert cliente.delete(f"/api/grupos/{grupo['id']}", headers=docente).status_code == 204
    detalle = cliente.get(f"/api/cuestionarios/{cuestionario_curso}", headers=docente).json()
    assert detalle["grupo_id"] is None
    assert cliente.get("/api/mis-cursos", headers=estudiante).json() == []


def test_eliminar_cuenta_de_estudiante_borra_su_matricula(cliente, grupo, estudiante, docente, sesion_factory):
    _unir(cliente, estudiante, grupo)
    assert cliente.request("DELETE", "/api/auth/cuenta", json={"password": PASSWORD}, headers=estudiante).status_code == 204
    with sesion_factory() as db:
        assert db.query(Matricula).count() == 0


# ---------- RA y Bloom en las preguntas ----------

def test_ras_elegibles_son_los_de_la_asignatura_del_grupo(cliente, docente, grupo, crear_cuestionario, estructura):
    cid = crear_cuestionario(docente)
    assert cliente.get(f"/api/cuestionarios/{cid}/ras", headers=docente).json() == []
    cliente.patch(f"/api/cuestionarios/{cid}", json={"grupo_id": grupo["id"]}, headers=docente)
    codigos = [r["codigo"] for r in cliente.get(f"/api/cuestionarios/{cid}/ras", headers=docente).json()]
    assert codigos == ["RA1", "RA2"]


def test_pregunta_valida_ra_y_bloom(cliente, docente, grupo, crear_cuestionario, estructura):
    cid = crear_cuestionario(docente)
    p = cliente.get(f"/api/cuestionarios/{cid}", headers=docente).json()["preguntas"][0]
    cuerpo = {"tipo": p["tipo"], "enunciado": p["enunciado"], "opciones": p["opciones"], "respuesta_correcta": p["respuesta_correcta"],
              "explicacion": p["explicacion"], "marca_tiempo": p["marca_tiempo"]}
    # sin grupo no se puede elegir RA
    assert cliente.put(f"/api/preguntas/{p['id']}", json={**cuerpo, "ra_id": estructura["ra1"]["id"]}, headers=docente).status_code == 400
    cliente.patch(f"/api/cuestionarios/{cid}", json={"grupo_id": grupo["id"]}, headers=docente)
    # RA que no es de la asignatura
    assert cliente.put(f"/api/preguntas/{p['id']}", json={**cuerpo, "ra_id": estructura["ra3"]["id"]}, headers=docente).status_code == 400
    assert cliente.put(f"/api/preguntas/{p['id']}", json={**cuerpo, "ra_id": estructura["ra_otro"]["id"]}, headers=docente).status_code == 400
    # Bloom inválido
    assert cliente.put(f"/api/preguntas/{p['id']}", json={**cuerpo, "nivel_bloom": "memorizar"}, headers=docente).status_code == 422
    r = cliente.put(f"/api/preguntas/{p['id']}", json={**cuerpo, "ra_id": estructura["ra2"]["id"], "nivel_bloom": "analizar"}, headers=docente)
    assert r.status_code == 200 and r.json()["ra_id"] == estructura["ra2"]["id"] and r.json()["nivel_bloom"] == "analizar"


def test_cambiar_de_grupo_limpia_los_ra_y_duplicar_los_conserva(cliente, docente, grupo, cuestionario_curso):
    copia = cliente.post(f"/api/cuestionarios/{cuestionario_curso}/duplicar", json={"modo": "aprendizaje"}, headers=docente).json()
    pregs = cliente.get(f"/api/cuestionarios/{copia['id']}", headers=docente).json()
    assert pregs["grupo_id"] == grupo["id"] and pregs["preguntas"][0]["ra_id"] is not None
    cliente.patch(f"/api/cuestionarios/{copia['id']}", json={"grupo_id": None}, headers=docente)
    limpio = cliente.get(f"/api/cuestionarios/{copia['id']}", headers=docente).json()
    assert all(p["ra_id"] is None for p in limpio["preguntas"])


def test_estudiante_no_ve_ra_ni_bloom_en_el_detalle(cliente, cuestionario_curso, estudiante, docente):
    est = cliente.get(f"/api/cuestionarios/{cuestionario_curso}", headers=estudiante).json()
    assert all(p["ra_id"] is None and p["nivel_bloom"] is None for p in est["preguntas"])
    doc = cliente.get(f"/api/cuestionarios/{cuestionario_curso}", headers=docente).json()
    assert doc["preguntas"][0]["nivel_bloom"] == "recordar"


def test_esquema_ia_acepta_nivel_bloom_opcional_y_el_prompt_lo_pide():
    base = {"tipo": "abierta", "enunciado": "¿Qué?", "respuesta_correcta": "x", "explicacion": "y"}
    assert PreguntaIA(**base).nivel_bloom is None
    assert PreguntaIA(**base, nivel_bloom="crear").nivel_bloom == "crear"
    with pytest.raises(ValueError):
        PreguntaIA(**base, nivel_bloom="inventar")
    assert "nivel_bloom" in construir_prompt("texto", 3)


def test_la_ia_guarda_el_nivel_de_bloom(cliente, docente, monkeypatch):
    from app.routers import procesar
    from tests.conftest import URL_VIDEO, resultado_falso

    def con_bloom(texto, n):
        r = resultado_falso(n)
        r.preguntas[0].nivel_bloom = "evaluar"
        return r, "falso"

    monkeypatch.setattr(procesar, "generar_con_respaldo", con_bloom)
    tarea = cliente.post("/api/procesar", json={"url": URL_VIDEO, "num_preguntas": 3}, headers=docente).json()
    cid = cliente.get(f"/api/tareas/{tarea['id']}", headers=docente).json()["cuestionario_id"]
    pregs = cliente.get(f"/api/cuestionarios/{cid}", headers=docente).json()["preguntas"]
    assert [p["nivel_bloom"] for p in pregs] == ["evaluar", None, None]


# ---------- Logro por RA y panel de coordinación ----------

def test_semaforo_umbrales():
    assert [semaforo(v) for v in (None, 70, 69.9, 50, 49.9, 0, 100)] == ["sin_datos", "verde", "amarillo", "amarillo", "rojo", "rojo", "verde"]


def _ras_por_codigo(resumen: dict) -> dict:
    return {r["codigo"]: r for r in resumen["ras"]}


def test_logro_por_ra_con_datos_conocidos(cliente, coordinador, grupo, cuestionario_curso, estudiante, otro_estudiante, tercer_estudiante, intentar):
    for h in (estudiante, otro_estudiante, tercer_estudiante):
        _unir(cliente, h, grupo)
    intentar(estudiante, cuestionario_curso, correctas=2)  # acierta P1 (RA1) y P2 (RA2)
    intentar(otro_estudiante, cuestionario_curso, correctas=1)  # acierta solo P1
    intentar(tercer_estudiante, cuestionario_curso, correctas=0)
    d = cliente.get("/api/coordinacion/resumen", headers=coordinador).json()
    ras = _ras_por_codigo(d)
    assert ras["RA1"]["logro"] == 66.7 and ras["RA1"]["semaforo"] == "amarillo" and ras["RA1"]["respuestas"] == 3 and ras["RA1"]["estudiantes"] == 3
    assert ras["RA2"]["logro"] == 33.3 and ras["RA2"]["semaforo"] == "rojo"
    assert ras["RA3"]["logro"] is None and ras["RA3"]["semaforo"] == "sin_datos"
    assert d["logro_global"] == 50.0 and d["respuestas"] == 6 and d["estudiantes"] == 3


def test_logro_verde_y_bloom(cliente, coordinador, grupo, cuestionario_curso, estudiante, intentar):
    _unir(cliente, estudiante, grupo)
    intentar(estudiante, cuestionario_curso, correctas=2)
    d = cliente.get("/api/coordinacion/resumen", headers=coordinador).json()
    assert _ras_por_codigo(d)["RA1"]["semaforo"] == "verde" and _ras_por_codigo(d)["RA2"]["logro"] == 100.0
    bloom = {b["nivel"]: b for b in d["bloom"]}
    assert len(d["bloom"]) == 6
    assert bloom["recordar"]["respuestas"] == 1 and bloom["recordar"]["logro"] == 100.0 and bloom["aplicar"]["preguntas"] == 1
    assert bloom["crear"]["logro"] is None
    asig = d["asignaturas"][0]
    assert asig["nombre"] == "Bases de Datos" and asig["grupos"][0]["nombre"] == "Grupo A" and asig["grupos"][0]["logro"] == 100.0
    assert len(d["tendencia"]) == 1 and d["tendencia"][0]["respuestas"] == 2


def test_solo_cuentan_estudiantes_matriculados(cliente, coordinador, grupo, cuestionario_curso, estudiante, otro_estudiante, intentar):
    _unir(cliente, estudiante, grupo)
    intentar(estudiante, cuestionario_curso, correctas=2)
    intentar(otro_estudiante, cuestionario_curso, correctas=0)  # no matriculado: no cuenta
    d = cliente.get("/api/coordinacion/resumen", headers=coordinador).json()
    assert d["estudiantes"] == 1 and d["logro_global"] == 100.0


def test_filtro_por_periodo(cliente, coordinador, docente, grupo, cuestionario_curso, estudiante, intentar, estructura):
    _unir(cliente, estudiante, grupo)
    intentar(estudiante, cuestionario_curso, correctas=2)
    cliente.post("/api/grupos", json={"asignatura_id": estructura["a1"]["id"], "periodo": "2026-1", "nombre": "Grupo B"}, headers=docente)
    d = cliente.get("/api/coordinacion/resumen", params={"periodo": "2026-1"}, headers=coordinador).json()
    assert d["periodos"] == ["2026-2", "2026-1"] and d["respuestas"] == 0 and d["logro_global"] is None
    assert [g["nombre"] for a in d["asignaturas"] for g in a["grupos"]] == ["Grupo B"]
    d = cliente.get("/api/coordinacion/resumen", params={"periodo": "2026-2"}, headers=coordinador).json()
    assert d["respuestas"] == 2


def test_alcance_del_coordinador_y_del_admin(cliente, admin, coordinador, estructura, sesion_factory):
    d = cliente.get("/api/coordinacion/resumen", headers=coordinador).json()
    assert d["programa_nombre"] == "Ingeniería de Sistemas" and [p["id"] for p in d["programas"]] == [estructura["p1"]["id"]]
    assert {r["programa"] for r in d["ras"]} == {"Ingeniería de Sistemas"}
    assert cliente.get("/api/coordinacion/resumen", params={"programa_id": estructura["p2"]["id"]}, headers=coordinador).status_code == 403
    a = cliente.get("/api/coordinacion/resumen", headers=admin).json()
    assert a["programa_nombre"] == "Todos los programas" and len(a["programas"]) == 2 and len(a["ras"]) == 4
    a2 = cliente.get("/api/coordinacion/resumen", params={"programa_id": estructura["p2"]["id"]}, headers=admin).json()
    assert [r["codigo"] for r in a2["ras"]] == ["RA1"] and a2["programa_nombre"] == "Administración"


def test_coordinador_sin_programa_recibe_400(cliente, sesion_factory):
    h = _con_rol(cliente, sesion_factory, "coordinador", "Sin Programa", "sinprog@prueba.com")
    r = cliente.get("/api/coordinacion/resumen", headers=h)
    assert r.status_code == 400 and "programa" in r.json()["detail"]


# ---------- Alertas tempranas ----------

def _codigos(alertas: list[dict]) -> dict:
    return {a["email"]: [m["codigo"] for m in a["motivos"]] for a in alertas}


def test_sin_alertas_para_un_estudiante_al_dia(cliente, grupo, estudiante, docente):
    _unir(cliente, estudiante, grupo)
    assert cliente.get("/api/alertas", headers=docente).json() == []


def test_alerta_por_inactividad(cliente, grupo, estudiante, docente, sesion_factory):
    _unir(cliente, estudiante, grupo)
    with sesion_factory() as db:
        db.query(Matricula).update({"creado_en": ahora() - timedelta(days=20)})
        db.commit()
    alertas = cliente.get("/api/alertas", headers=docente).json()
    assert _codigos(alertas) == {"estudiante@prueba.com": ["inactividad"]}
    assert "20 días" in alertas[0]["motivos"][0]["texto"] and alertas[0]["nivel"] == "medio"


def test_inactividad_no_salta_antes_de_14_dias(cliente, grupo, estudiante, docente, sesion_factory):
    _unir(cliente, estudiante, grupo)
    with sesion_factory() as db:
        db.query(Matricula).update({"creado_en": ahora() - timedelta(days=13)})
        db.commit()
    assert cliente.get("/api/alertas", headers=docente).json() == []


def test_alerta_por_bajo_promedio_inicial(cliente, grupo, cuestionario_curso, estudiante, docente, intentar):
    _unir(cliente, estudiante, grupo)
    intentar(estudiante, cuestionario_curso, correctas=0)
    assert _codigos(cliente.get("/api/alertas", headers=docente).json()) == {"estudiante@prueba.com": ["bajo_promedio"]}


def test_sin_alerta_con_buen_promedio(cliente, grupo, cuestionario_curso, estudiante, docente, intentar):
    _unir(cliente, estudiante, grupo)
    intentar(estudiante, cuestionario_curso, correctas=2)
    assert cliente.get("/api/alertas", headers=docente).json() == []


def test_alerta_por_repasos_vencidos(cliente, grupo, cuestionario_curso, estudiante, docente, sesion_factory):
    _unir(cliente, estudiante, grupo)
    with sesion_factory() as db:
        uid = db.query(Usuario).filter_by(email="estudiante@prueba.com").one().id
        for _ in range(2):
            db.add(Repaso(usuario_id=uid, cuestionario_id=cuestionario_curso, disponible_desde=ahora() - timedelta(days=1)))
        db.commit()
    assert _codigos(cliente.get("/api/alertas", headers=docente).json()) == {"estudiante@prueba.com": ["repasos_vencidos"]}


def test_un_repaso_vencido_no_alcanza(cliente, grupo, cuestionario_curso, estudiante, docente, sesion_factory):
    _unir(cliente, estudiante, grupo)
    with sesion_factory() as db:
        uid = db.query(Usuario).filter_by(email="estudiante@prueba.com").one().id
        db.add(Repaso(usuario_id=uid, cuestionario_id=cuestionario_curso, disponible_desde=ahora() - timedelta(days=1)))
        db.add(Repaso(usuario_id=uid, cuestionario_id=cuestionario_curso, disponible_desde=ahora() + timedelta(days=3)))
        db.commit()
    assert cliente.get("/api/alertas", headers=docente).json() == []


def _intento_directo(db, uid, cid, puntaje, total, tipo, hace_dias):
    db.add(Intento(usuario_id=uid, cuestionario_id=cid, puntaje=puntaje, total=total, finalizado=True, tipo=tipo,
                   creado_en=ahora() - timedelta(days=hace_dias)))


def test_alerta_por_caida_entre_ultimos_intentos(cliente, grupo, cuestionario_curso, estudiante, docente, sesion_factory):
    _unir(cliente, estudiante, grupo)
    with sesion_factory() as db:
        uid = db.query(Usuario).filter_by(email="estudiante@prueba.com").one().id
        _intento_directo(db, uid, cuestionario_curso, 10, 10, "inicial", 3)  # 100 %
        _intento_directo(db, uid, cuestionario_curso, 7, 10, "practica", 1)  # 70 %: baja 30 puntos
        db.commit()
    alertas = cliente.get("/api/alertas", headers=docente).json()
    assert _codigos(alertas) == {"estudiante@prueba.com": ["caida"]}
    assert "30 puntos" in alertas[0]["motivos"][0]["texto"]


def test_caida_menor_a_20_puntos_no_alerta(cliente, grupo, cuestionario_curso, estudiante, docente, sesion_factory):
    _unir(cliente, estudiante, grupo)
    with sesion_factory() as db:
        uid = db.query(Usuario).filter_by(email="estudiante@prueba.com").one().id
        _intento_directo(db, uid, cuestionario_curso, 10, 10, "inicial", 3)
        _intento_directo(db, uid, cuestionario_curso, 9, 10, "practica", 1)  # baja 10 puntos
        db.commit()
    assert cliente.get("/api/alertas", headers=docente).json() == []


def test_nivel_alto_con_dos_motivos_y_orden(cliente, grupo, cuestionario_curso, estudiante, otro_estudiante, docente, sesion_factory):
    _unir(cliente, estudiante, grupo)
    _unir(cliente, otro_estudiante, grupo)
    with sesion_factory() as db:
        uid = db.query(Usuario).filter_by(email="estudiante@prueba.com").one().id
        _intento_directo(db, uid, cuestionario_curso, 2, 10, "inicial", 1)  # promedio 20 %
        for _ in range(2):
            db.add(Repaso(usuario_id=uid, cuestionario_id=cuestionario_curso, disponible_desde=ahora() - timedelta(days=1)))
        db.query(Matricula).filter(Matricula.estudiante_id != uid).update({"creado_en": ahora() - timedelta(days=30)})
        db.commit()
    alertas = cliente.get("/api/alertas", headers=docente).json()
    assert [a["nivel"] for a in alertas] == ["alto", "medio"]
    assert alertas[0]["email"] == "estudiante@prueba.com" and len(alertas[0]["motivos"]) == 2


def test_atender_oculta_la_alerta_hasta_que_haya_un_motivo_nuevo(cliente, grupo, cuestionario_curso, estudiante, docente, sesion_factory, intentar):
    _unir(cliente, estudiante, grupo)
    intentar(estudiante, cuestionario_curso, correctas=0)
    alerta = cliente.get("/api/alertas", headers=docente).json()[0]
    r = cliente.post("/api/alertas/atender", json={"grupo_id": alerta["grupo_id"], "estudiante_id": alerta["estudiante_id"], "nota": "Hablé con él"}, headers=docente)
    assert r.status_code == 201 and r.json()["nota"] == "Hablé con él" and r.json()["motivos"] == "bajo_promedio"
    assert cliente.get("/api/alertas", headers=docente).json() == []
    # no se puede atender dos veces la misma alerta
    assert cliente.post("/api/alertas/atender", json={"grupo_id": alerta["grupo_id"], "estudiante_id": alerta["estudiante_id"]}, headers=docente).status_code == 404
    # aparece un motivo nuevo (inactividad): la alerta vuelve
    with sesion_factory() as db:
        db.query(Matricula).update({"creado_en": ahora() - timedelta(days=40)})
        db.query(Intento).update({"creado_en": ahora() - timedelta(days=30)})
        db.commit()
    assert _codigos(cliente.get("/api/alertas", headers=docente).json()) == {"estudiante@prueba.com": ["inactividad", "bajo_promedio"]}
    assert len(cliente.get("/api/alertas/seguimientos", headers=docente).json()) == 1


def test_alertas_por_alcance(cliente, grupo, estudiante, docente, coordinador, admin, sesion_factory, estructura):
    _unir(cliente, estudiante, grupo)
    with sesion_factory() as db:
        db.query(Matricula).update({"creado_en": ahora() - timedelta(days=20)})
        db.commit()
    otro = _registrar(cliente, "docente", "Otro Docente", "otro@prueba.com")
    assert len(cliente.get("/api/alertas", headers=docente).json()) == 1
    assert cliente.get("/api/alertas", headers=otro).json() == []
    assert len(cliente.get("/api/alertas", headers=coordinador).json()) == 1
    assert len(cliente.get("/api/alertas", headers=admin).json()) == 1
    # el coordinador de otro programa no ve las alertas de este
    ajeno = _con_rol(cliente, sesion_factory, "coordinador", "Coord Dos", "coord2@prueba.com", estructura["p2"]["id"])
    assert cliente.get("/api/alertas", headers=ajeno).json() == []
    assert cliente.post("/api/alertas/atender", json={"grupo_id": grupo["id"], "estudiante_id": 1}, headers=otro).status_code == 404


# ---------- Reportes PDF ----------

def test_reporte_ra_pdf(cliente, coordinador, grupo, cuestionario_curso, estudiante, intentar):
    _unir(cliente, estudiante, grupo)
    intentar(estudiante, cuestionario_curso, correctas=2)
    r = cliente.get("/api/coordinacion/reporte-ra.pdf", params={"periodo": "2026-2"}, headers=coordinador)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF") and len(r.content) > 2000
    assert "attachment" in r.headers["content-disposition"]


def test_reporte_ra_pdf_sin_datos_tambien_se_genera(cliente, admin):
    r = cliente.get("/api/coordinacion/reporte-ra.pdf", headers=admin)
    assert r.status_code == 200 and r.content.startswith(b"%PDF")


def test_reporte_cuestionario_pdf(cliente, docente, cuestionario_curso, grupo, estudiante, intentar):
    _unir(cliente, estudiante, grupo)
    intentar(estudiante, cuestionario_curso, correctas=1)
    r = cliente.get(f"/api/cuestionarios/{cuestionario_curso}/reporte.pdf", headers=docente)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")


def test_reporte_cuestionario_pdf_permisos_y_sin_grupo(cliente, docente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(docente)
    assert cliente.get(f"/api/cuestionarios/{cid}/reporte.pdf", headers=docente).content.startswith(b"%PDF")  # sin grupo
    assert cliente.get(f"/api/cuestionarios/{cid}/reporte.pdf", headers=estudiante).status_code == 403
    otro = _registrar(cliente, "docente", "Otro Docente", "otro@prueba.com")
    assert cliente.get(f"/api/cuestionarios/{cid}/reporte.pdf", headers=otro).status_code == 403
    assert cliente.get("/api/cuestionarios/9999/reporte.pdf", headers=docente).status_code == 404


# ---------- Migración ----------

def test_migracion_agrega_columnas_del_sprint_6(tmp_path, monkeypatch):
    motor = create_engine(f"sqlite:///{tmp_path / 'vieja.db'}")
    with motor.begin() as con:
        con.execute(text("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, rol VARCHAR(20))"))
        con.execute(text("CREATE TABLE cuestionarios (id INTEGER PRIMARY KEY, publicado BOOLEAN, creado_en DATETIME)"))
        con.execute(text("CREATE TABLE videos (id INTEGER PRIMARY KEY, youtube_id VARCHAR(20), archivo VARCHAR(100))"))
        con.execute(text("CREATE TABLE tareas (id VARCHAR(32) PRIMARY KEY)"))
        con.execute(text("CREATE TABLE intentos (id INTEGER PRIMARY KEY, usuario_id INTEGER, cuestionario_id INTEGER, "
                         "finalizado BOOLEAN, creado_en DATETIME)"))
        con.execute(text("CREATE TABLE preguntas (id INTEGER PRIMARY KEY, enunciado TEXT)"))
    monkeypatch.setattr(modulo_db, "engine", motor)
    modulo_db._migrar_columnas()
    modulo_db._migrar_columnas()  # idempotente
    from sqlalchemy import inspect
    insp = inspect(motor)
    assert {"programa_id"} <= {c["name"] for c in insp.get_columns("usuarios")}
    assert {"grupo_id"} <= {c["name"] for c in insp.get_columns("cuestionarios")}
    assert {"ra_id", "nivel_bloom"} <= {c["name"] for c in insp.get_columns("preguntas")}


def test_modelos_nuevos_se_crean_y_relacionan(sesion_factory):
    from app.modelos import Asignatura, Facultad, Programa, ResultadoAprendizaje
    with sesion_factory() as db:
        f = Facultad(nombre="F")
        p = Programa(facultad=f, nombre="P", codigo="P1")
        ra = ResultadoAprendizaje(programa=p, codigo="RA1", descripcion="d")
        a = Asignatura(programa=p, nombre="A", codigo="A1", semestre=2, resultados=[ra])
        db.add_all([f, p, ra, a])
        db.commit()
        assert [x.codigo for x in a.resultados] == ["RA1"] and p.facultad.nombre == "F"
        assert db.query(AlertaSeguimiento).count() == 0 and db.query(Cuestionario).count() == 0 and db.query(Grupo).count() == 0
