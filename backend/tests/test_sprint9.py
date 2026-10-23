"""Pruebas del Sprint 9: tutorial de primer uso, datos de demostración, calibración de la calificación de abiertas
y compatibilidad de los modelos con PostgreSQL. Sin internet ni IA real."""
import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sembrar_demo  # noqa: E402

from app.db import Base, _COLUMNAS_NUEVAS  # noqa: E402
from app.modelos import (  # noqa: E402
    Cuestionario,
    Grupo,
    Intento,
    Matricula,
    Notificacion,
    Pregunta,
    PreguntaBanco,
    RegistroDemo,
    RespuestaSUS,
    SesionVivo,
    Usuario,
)
from app.services import calificacion  # noqa: E402
from app.services.calificacion import CalificacionIA, calificar_abierta, construir_prompt, nivel_por_puntaje  # noqa: E402
from tests.conftest import PASSWORD, _registrar  # noqa: E402

CLAVE_DEMO = "Demo12345"


def entrar(cliente, email):
    r = cliente.post("/api/auth/login", json={"email": email, "password": CLAVE_DEMO})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture()
def demo(sesion_factory):
    with sesion_factory() as db:
        resumen = sembrar_demo.sembrar(db, verboso=False)
    assert resumen["sembrado"] is True
    return resumen


def contar(sesion_factory, modelo):
    with sesion_factory() as db:
        return db.scalar(select(func.count()).select_from(modelo))


# ---------- Tutorial de primer uso ----------

def test_tutorial_visto_vacio_por_defecto(cliente, estudiante):
    assert cliente.get("/api/auth/yo", headers=estudiante).json()["tutorial_visto"] == []


def test_tutorial_se_marca_y_persiste(cliente, estudiante):
    r = cliente.put("/api/auth/tutorial", json={"visto": True}, headers=estudiante)
    assert r.status_code == 200 and r.json()["tutorial_visto"] == ["estudiante"]
    assert cliente.get("/api/auth/yo", headers=estudiante).json()["tutorial_visto"] == ["estudiante"]


def test_tutorial_se_puede_repetir_y_no_duplica(cliente, docente):
    for _ in range(2):
        r = cliente.put("/api/auth/tutorial", json={"visto": True}, headers=docente)
    assert r.json()["tutorial_visto"] == ["docente"]
    r = cliente.put("/api/auth/tutorial", json={"visto": False}, headers=docente)
    assert r.json()["tutorial_visto"] == []


def test_tutorial_es_por_rol(cliente, sesion_factory, docente):
    cliente.put("/api/auth/tutorial", json={"visto": True}, headers=docente)
    with sesion_factory() as db:  # si el usuario pasa a coordinador, su tutorial de coordinador aún no se ha visto
        u = db.scalar(select(Usuario).where(Usuario.email == "docente@prueba.com"))
        u.rol = "coordinador"
        db.commit()
    r = cliente.get("/api/auth/yo", headers=docente).json()
    assert "coordinador" not in r["tutorial_visto"] and r["tutorial_visto"] == ["docente"]
    r = cliente.put("/api/auth/tutorial", json={"visto": True}, headers=docente).json()
    assert sorted(r["tutorial_visto"]) == ["coordinador", "docente"]


def test_tutorial_exige_sesion(cliente):
    assert cliente.put("/api/auth/tutorial", json={"visto": True}).status_code in (401, 403)


def test_columna_tutorial_en_migracion():
    assert any(n == "tutorial_visto" for n, _ in _COLUMNAS_NUEVAS["usuarios"])


# ---------- Sembrado de demostración ----------

def test_sembrado_crea_estructura_esperada(sesion_factory, demo):
    with sesion_factory() as db:
        estudiantes = db.scalars(select(Usuario).where(Usuario.email.like("%@demo.com"), Usuario.rol == "estudiante")).all()
        assert len(estudiantes) == 25  # 24 sembrados + estudiante@demo.com
        assert all(u.acepta_tratamiento_datos for u in estudiantes)
        grupos = db.scalars(select(Grupo).where(Grupo.periodo == "2026-2")).all()
        assert len(grupos) == 4  # Grupo A de sembrar_estructura + 3 de la demo
        cuestionarios = db.scalars(select(Cuestionario).where(Cuestionario.proveedor_ia == "demo")).all()
        assert len(cuestionarios) == 5 and all(c.publicado and c.num_preguntas == 8 for c in cuestionarios)
        assert sum(1 for c in cuestionarios if c.modo == "control") == 1
        for c in cuestionarios:
            assert len(c.preguntas) == 8
            assert all(p.ra_id and p.nivel_bloom and p.explicacion and p.marca_tiempo for p in c.preguntas)
            assert all(json.loads(p.verificacion)["estado"] == "verificada" for p in c.preguntas)
            assert sorted({p.tipo for p in c.preguntas}) == ["abierta", "opcion_multiple", "verdadero_falso"]


def test_sembrado_es_idempotente(sesion_factory, demo):
    antes = {m: contar(sesion_factory, m) for m in (Usuario, Intento, Cuestionario, Pregunta, RegistroDemo, Notificacion)}
    with sesion_factory() as db:
        assert sembrar_demo.sembrar(db, verboso=False) == {"sembrado": False}
    assert antes == {m: contar(sesion_factory, m) for m in antes}


def test_reset_borra_solo_lo_sembrado(cliente, sesion_factory, docente, crear_cuestionario):
    cid = crear_cuestionario(docente)  # dato ajeno a la demo
    with sesion_factory() as db:
        sembrar_demo.sembrar(db, verboso=False)
    base = contar(sesion_factory, Usuario)
    with sesion_factory() as db:
        borrados = sembrar_demo.reset(db)
    assert borrados["usuarios"] == 24 and borrados["cuestionarios"] == 5
    with sesion_factory() as db:
        assert db.get(Cuestionario, cid) is not None  # el cuestionario ajeno sigue
        assert db.scalar(select(Usuario).where(Usuario.email == "docente@prueba.com")) is not None
        assert db.scalar(select(Usuario).where(Usuario.email == "docente@demo.com")) is not None  # base de sembrar_estructura
        assert db.scalar(select(func.count()).select_from(Usuario)) == base - 24
        assert db.scalar(select(func.count()).select_from(RegistroDemo)) == 0
        assert db.scalar(select(func.count()).select_from(Intento).where(Intento.cuestionario_id != cid)) == 0
        assert db.scalar(select(func.count()).select_from(SesionVivo)) == 0
        assert db.scalar(select(func.count()).select_from(RespuestaSUS)) == 0


def test_reset_y_volver_a_sembrar(sesion_factory, demo):
    with sesion_factory() as db:
        sembrar_demo.reset(db)
        assert sembrar_demo.sembrar(db, verboso=False)["sembrado"] is True
    assert contar(sesion_factory, Cuestionario) == 5


def test_reset_sin_sembrar_no_falla(sesion_factory):
    with sesion_factory() as db:
        assert sembrar_demo.reset(db) == {}


def test_sembrado_produce_alertas(cliente, demo):
    docente = entrar(cliente, "docente@demo.com")
    alertas = cliente.get("/api/alertas", headers=docente).json()
    assert len(alertas) >= 6
    codigos = {m["codigo"] for a in alertas for m in a["motivos"]}
    assert {"inactividad", "bajo_promedio", "repasos_vencidos", "caida"} <= codigos
    assert any(a["nivel"] == "alto" for a in alertas) and any(a["nivel"] == "medio" for a in alertas)


def test_sembrado_produce_analisis_de_items(cliente, sesion_factory, demo):
    docente = entrar(cliente, "docente@demo.com")
    with sesion_factory() as db:
        ids = {c.titulo: c.id for c in db.scalars(select(Cuestionario).where(Cuestionario.proveedor_ia == "demo"))}
    r = cliente.get(f"/api/cuestionarios/{ids['Bases de datos relacionales: tablas, claves y SQL básico']}/resultados", headers=docente).json()
    cerradas = [i for i in r["items"] if i["suficiente"]]
    assert len(cerradas) == 7 and all(i["n"] >= 5 for i in cerradas)
    assert all(i["p"] is not None and i["d"] is not None for i in cerradas)
    assert sum(1 for i in cerradas if i["r_pb"] is not None) >= 5
    # En el conjunto de la demo hay ítems que conviene revisar y la ganancia (primer vs. último intento) tiene datos
    revisados = 0
    for titulo, cid in ids.items():
        res = cliente.get(f"/api/cuestionarios/{cid}/resultados", headers=docente).json()
        revisados += sum(1 for i in res["items"] if i["revisar"])
    assert revisados >= 1
    r2 = cliente.get(f"/api/cuestionarios/{ids['Normalización de bases de datos: 1FN, 2FN y 3FN']}/resultados", headers=docente).json()
    assert r2["ganancia"]["estudiantes"] > 0


def test_sembrado_produce_retencion_y_comparacion(cliente, sesion_factory, demo):
    docente = entrar(cliente, "docente@demo.com")
    with sesion_factory() as db:
        cs = [c for c in db.scalars(select(Cuestionario).where(Cuestionario.proveedor_ia == "demo")) if c.titulo.startswith("Algoritmos")]
    control = next(c.id for c in cs if c.modo == "control")
    normal = next(c.id for c in cs if c.modo == "aprendizaje")
    r = cliente.get("/api/comparar", params={"a": normal, "b": control}, headers=docente).json()
    assert r["a"]["inicial"]["n"] >= 5 and r["b"]["inicial"]["n"] >= 5
    assert r["a"]["retencion"]["n"] >= 3 and r["b"]["retencion"]["n"] >= 3
    assert r["a"]["retencion"]["media"] > r["b"]["retencion"]["media"]
    res = cliente.get(f"/api/cuestionarios/{normal}/resultados", headers=docente).json()
    assert res["retencion"]


def test_coordinacion_con_datos(cliente, demo):
    r = cliente.get("/api/coordinacion/resumen", headers=entrar(cliente, "coordinador@demo.com")).json()
    assert r["respuestas"] > 200 and r["estudiantes"] >= 20
    con_datos = [x for x in r["ras"] if x["logro"] is not None]
    assert len(con_datos) >= 4 and r["logro_global"] is not None
    assert len(r["tendencia"]) >= 4  # varias semanas de actividad
    assert len({x["semaforo"] for x in con_datos}) >= 2


def test_sus_realista(cliente, demo):
    r = cliente.get("/api/sus/resumen", headers=entrar(cliente, "docente@demo.com")).json()
    assert r["n"] == 15 and 70 <= r["promedio"] <= 80


def test_clases_en_vivo_historicas_y_banco(cliente, sesion_factory, demo):
    docente = entrar(cliente, "docente@demo.com")
    with sesion_factory() as db:
        sesiones = db.scalars(select(SesionVivo)).all()
        assert len(sesiones) == 2 and all(s.estado == "finalizada" for s in sesiones)
        assert len(db.scalars(select(PreguntaBanco)).all()) == 12
        cid = sesiones[0].cuestionario_id
    historial = cliente.get(f"/api/cuestionarios/{cid}/vivo", headers=docente).json()
    assert len(historial) == 1 and historial[0]["participantes"] >= 8 and historial[0]["promedio_acierto"] is not None


def test_abiertas_con_nota_sugerida_y_aprobadas(sesion_factory, demo):
    with sesion_factory() as db:
        sugeridas = aprobadas = 0
        for i in db.scalars(select(Intento)):
            for r in json.loads(i.respuestas_json):
                if r.get("ia"):
                    sugeridas += 1
                    assert nivel_por_puntaje(r["ia"]["puntaje"]) == r["ia"]["nivel"]
                    aprobadas += 1 if r.get("nota_final") is not None else 0
    assert sugeridas > 30 and 0 < aprobadas < sugeridas


def test_estudiantes_de_la_demo_pueden_entrar(cliente, demo):
    assert entrar(cliente, "valentina.gomez@demo.com")


# ---------- Calibración de la calificación de abiertas ----------

def test_prompt_calibrado_por_ideas_clave():
    p = construir_prompt("¿Qué es X?", "X es A y B.", "", "respuesta")
    assert "IDEAS CLAVE" in p and "entre 2 y 4" in p and "proporcional" in p
    assert "NO penalices sinónimos" in p and "redacción informal" in p
    assert "insuficiente 0-39, basico 40-69, bueno 70-89, excelente 90-100" in p
    assert "PRIMERO lo que está bien" in p
    assert "respuesta" in p.split("<<<")[1] and "dato" in p.lower()


@pytest.mark.parametrize("nota,nivel", [(39, "insuficiente"), (40, "basico"), (69, "basico"), (70, "bueno"), (89, "bueno"), (90, "excelente")])
def test_umbrales_nuevos_de_nivel(nota, nivel):
    assert nivel_por_puntaje(nota) == nivel


def test_calificar_abierta_nivel_coherente_con_umbral_nuevo(ia_generica):
    ia_generica["manejador"] = lambda prompt, esquema: CalificacionIA(
        puntaje=72, nivel="excelente", retroalimentacion="Bien.", falto="Un detalle.")
    r = calificar_abierta("¿Qué es X?", "X es A y B.", "", "A")
    assert r["puntaje"] == 72 and r["nivel"] == "bueno"  # el nivel se deriva de la nota, no de lo que diga la IA
    assert "NO penalices" in ia_generica["prompts"][-1]


def test_rubrica_documenta_los_cuatro_niveles():
    assert [n for _, n, _ in calificacion.RUBRICA] == ["excelente", "bueno", "basico", "insuficiente"]
    assert [m for m, _, _ in calificacion.RUBRICA] == [90, 70, 40, 0]


# ---------- Compatibilidad con PostgreSQL ----------

def test_modelos_compilan_para_postgresql():
    """Ningún tipo ni constructor de los modelos es exclusivo de SQLite: el DDL se genera para PostgreSQL."""
    from app import modelos  # noqa: F401

    dialecto = postgresql.dialect()
    for tabla in Base.metadata.sorted_tables:
        ddl = str(CreateTable(tabla).compile(dialect=dialecto))
        assert "CREATE TABLE" in ddl and "AUTOINCREMENT" not in ddl
    assert len(Base.metadata.sorted_tables) >= 24
