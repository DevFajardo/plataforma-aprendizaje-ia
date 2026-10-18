"""Pruebas de la API con BD temporal y simulacros de transcripción/IA."""
from tests.conftest import PASSWORD

MEJOR = [5, 1, 5, 1, 5, 1, 5, 1, 5, 1]


# ---------- Autenticación ----------

def test_registro_login_y_yo(cliente):
    r = cliente.post("/api/auth/registro", json={"nombre": "Ana", "email": "Ana@Correo.com", "password": PASSWORD, "acepta_tratamiento_datos": True})
    assert r.status_code == 201
    assert r.json()["usuario"]["rol"] == "estudiante"
    assert r.json()["usuario"]["email"] == "ana@correo.com"
    r = cliente.post("/api/auth/login", json={"email": "ana@correo.com", "password": PASSWORD})
    assert r.status_code == 200
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    assert cliente.get("/api/auth/yo", headers=h).json()["nombre"] == "Ana"


def test_registro_duplicado_409_y_clave_corta_422(cliente):
    datos = {"nombre": "Ana", "email": "ana@correo.com", "password": PASSWORD, "acepta_tratamiento_datos": True}
    assert cliente.post("/api/auth/registro", json=datos).status_code == 201
    assert cliente.post("/api/auth/registro", json=datos).status_code == 409
    assert cliente.post("/api/auth/registro", json={**datos, "email": "b@c.com", "password": "corta"}).status_code == 422


def test_login_incorrecto_y_rutas_sin_token_401(cliente, estudiante):
    assert cliente.post("/api/auth/login", json={"email": "estudiante@prueba.com", "password": "mala-clave"}).status_code == 401
    assert cliente.get("/api/cuestionarios").status_code == 401
    assert cliente.get("/api/estadisticas/yo").status_code == 401
    assert cliente.get("/api/cuestionarios", headers={"Authorization": "Bearer falso"}).status_code == 401


# ---------- Procesamiento y visibilidad ----------

def test_procesar_url_invalida_400(cliente, estudiante):
    r = cliente.post("/api/procesar", json={"url": "https://example.com/x", "num_preguntas": 3}, headers=estudiante)
    assert r.status_code == 400


def test_procesar_llega_a_listo_con_mocks(cliente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(estudiante)
    c = cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).json()
    assert c["titulo"] == "Cuestionario de prueba"
    assert c["proveedor_ia"] == "falso"
    assert len(c["preguntas"]) == 3
    assert c["es_creador"] is True


def test_fechas_se_serializan_con_zona_horaria(cliente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(estudiante)
    c = cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).json()
    assert c["creado_en"].endswith(("Z", "+00:00"))
    lista = cliente.get("/api/cuestionarios", headers=estudiante).json()
    assert lista[0]["creado_en"].endswith(("Z", "+00:00"))


def test_estudiante_no_ve_borrador_y_ve_publicado_sin_respuestas(cliente, docente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(docente)
    assert cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).status_code == 403
    assert cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True}, headers=docente).status_code == 200
    r = cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante)
    assert r.status_code == 200
    d = r.json()
    assert d["es_creador"] is False and d["codigo_compartir"] is None
    assert all(p["respuesta_correcta"] is None and p["explicacion"] is None for p in d["preguntas"])


def test_publicar_es_solo_para_docentes_403(cliente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(estudiante)
    assert cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True}, headers=estudiante).status_code == 403


def test_otro_docente_no_puede_editar_403(cliente, docente, crear_cuestionario):
    cid = crear_cuestionario(docente)
    otro = cliente.post("/api/auth/registro", json={"nombre": "Otro", "email": "otro@prueba.com", "password": PASSWORD, "rol": "docente", "acepta_tratamiento_datos": True}).json()
    h = {"Authorization": f"Bearer {otro['token']}"}
    assert cliente.patch(f"/api/cuestionarios/{cid}", json={"titulo": "Robado"}, headers=h).status_code == 403


def test_compartir_por_codigo(cliente, docente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(docente)
    codigo = cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True}, headers=docente).json()["codigo_compartir"]
    r = cliente.get(f"/api/compartido/{codigo.lower()}", headers=estudiante)
    assert r.status_code == 200 and r.json()["cuestionario_id"] == cid
    assert cliente.get("/api/compartido/ZZZZZZ", headers=estudiante).status_code == 404
    cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": False}, headers=docente)
    assert cliente.get(f"/api/compartido/{codigo}", headers=estudiante).status_code == 404


# ---------- Intentos ----------

def test_intento_completo_y_puntaje(cliente, estudiante, crear_cuestionario, intentar):
    cid = crear_cuestionario(estudiante)
    r = intentar(estudiante, cid, correctas=2)
    assert (r["puntaje"], r["total"], r["porcentaje"], r["finalizado"]) == (2, 2, 100.0, True)
    r = intentar(estudiante, cid, correctas=1)
    assert (r["puntaje"], r["total"], r["porcentaje"]) == (1, 2, 50.0)
    assert len(cliente.get("/api/intentos", headers=estudiante).json()) == 2


def test_responder_dos_veces_409(cliente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(estudiante)
    c = cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).json()
    intento = cliente.post(f"/api/cuestionarios/{cid}/intentos", headers=estudiante).json()["id"]
    cuerpo = {"pregunta_id": c["preguntas"][0]["id"], "respuesta": "B"}
    r1 = cliente.post(f"/api/intentos/{intento}/responder", json=cuerpo, headers=estudiante)
    assert r1.status_code == 200 and r1.json()["correcta"] is True
    assert cliente.post(f"/api/intentos/{intento}/responder", json=cuerpo, headers=estudiante).status_code == 409


def test_no_se_puede_responder_un_intento_ajeno_ni_finalizado(cliente, estudiante, otro_estudiante, crear_cuestionario):
    cid = crear_cuestionario(estudiante)
    c = cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).json()
    intento = cliente.post(f"/api/cuestionarios/{cid}/intentos", headers=estudiante).json()["id"]
    cuerpo = {"pregunta_id": c["preguntas"][0]["id"], "respuesta": "B"}
    assert cliente.post(f"/api/intentos/{intento}/responder", json=cuerpo, headers=otro_estudiante).status_code == 404
    cliente.post(f"/api/intentos/{intento}/finalizar", headers=estudiante)
    assert cliente.post(f"/api/intentos/{intento}/responder", json=cuerpo, headers=estudiante).status_code == 409


# ---------- Edición validada ----------

def test_edicion_de_pregunta_validada_422(cliente, docente, crear_cuestionario):
    cid = crear_cuestionario(docente)
    c = cliente.get(f"/api/cuestionarios/{cid}", headers=docente).json()
    pid = c["preguntas"][0]["id"]
    malo = {"tipo": "opcion_multiple", "enunciado": "¿X?", "opciones": ["a", "b"], "respuesta_correcta": "z"}
    assert cliente.put(f"/api/preguntas/{pid}", json=malo, headers=docente).status_code == 422
    repetidas = {**malo, "opciones": ["a", "a"], "respuesta_correcta": "a"}
    assert cliente.put(f"/api/preguntas/{pid}", json=repetidas, headers=docente).status_code == 422
    r = cliente.put(f"/api/preguntas/{pid}", json={**malo, "respuesta_correcta": "a"}, headers=docente)
    assert r.status_code == 200 and r.json()["respuesta_correcta"] == "a"


# ---------- Resultados, ganancia de aprendizaje y CSV ----------

def _preparar_resultados(cliente, docente, estudiante, crear_cuestionario, intentar):
    cid = crear_cuestionario(docente)
    cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True}, headers=docente)
    intentar(estudiante, cid, correctas=1)  # primer intento: 50 %
    intentar(estudiante, cid, correctas=2)  # último intento: 100 %
    return cid


def test_resultados_y_ganancia_de_aprendizaje(cliente, docente, estudiante, crear_cuestionario, intentar):
    cid = _preparar_resultados(cliente, docente, estudiante, crear_cuestionario, intentar)
    r = cliente.get(f"/api/cuestionarios/{cid}/resultados", headers=docente).json()
    assert r["total_intentos"] == 2 and r["estudiantes_unicos"] == 1 and r["promedio_porcentaje"] == 75.0
    g = r["ganancia"]
    assert g["estudiantes"] == 1
    assert (g["promedio_primer_intento"], g["promedio_ultimo_intento"], g["diferencia_puntos"]) == (50.0, 100.0, 50.0)
    assert r["intentos"][0]["fecha"].endswith(("Z", "+00:00"))


def test_ganancia_ignora_estudiantes_con_un_solo_intento(cliente, docente, estudiante, otro_estudiante, crear_cuestionario, intentar):
    cid = _preparar_resultados(cliente, docente, estudiante, crear_cuestionario, intentar)
    intentar(otro_estudiante, cid, correctas=2)
    g = cliente.get(f"/api/cuestionarios/{cid}/resultados", headers=docente).json()["ganancia"]
    assert g["estudiantes"] == 1


def test_resultados_solo_docentes_403(cliente, estudiante, crear_cuestionario):
    cid = crear_cuestionario(estudiante)
    assert cliente.get(f"/api/cuestionarios/{cid}/resultados", headers=estudiante).status_code == 403


def test_csv_con_bom_y_ganancia(cliente, docente, estudiante, crear_cuestionario, intentar):
    cid = _preparar_resultados(cliente, docente, estudiante, crear_cuestionario, intentar)
    r = cliente.get(f"/api/cuestionarios/{cid}/resultados.csv", headers=docente)
    assert r.status_code == 200
    assert r.content.startswith(b"\xef\xbb\xbf")
    texto = r.content.decode("utf-8-sig")
    assert "Ganancia de aprendizaje" in texto and "Estudiante Uno" in texto


def test_csv_neutraliza_formulas(cliente, docente, crear_cuestionario, intentar):
    r = cliente.post("/api/auth/registro", json={"nombre": "=CMD()", "email": "x@prueba.com", "password": PASSWORD, "acepta_tratamiento_datos": True}).json()
    h = {"Authorization": f"Bearer {r['token']}"}
    cid = crear_cuestionario(docente)
    cliente.post(f"/api/cuestionarios/{cid}/publicar", json={"publicado": True}, headers=docente)
    intentar(h, cid)
    texto = cliente.get(f"/api/cuestionarios/{cid}/resultados.csv", headers=docente).content.decode("utf-8-sig")
    assert "'=CMD()" in texto


# ---------- Medios y borrado de archivos ----------

def test_medios_rechaza_path_traversal_y_nombres_raros(cliente):
    for nombre in ["..%2F..%2F.env", "..%5C..%5C.env", "archivo.mp4", "%2e%2e%2f%2e%2e%2fdatos.db", "a" * 32 + ".exe"]:
        r = cliente.get(f"/api/medios/{nombre}")
        assert r.status_code in (400, 404), (nombre, r.status_code)
    assert cliente.get("/api/medios/" + "a" * 32 + ".mp4").status_code == 404


def test_borrar_cuestionario_de_archivo_elimina_el_archivo(cliente, estudiante, tmp_path):
    r = cliente.post("/api/procesar/archivo", files={"archivo": ("clase.mp3", b"datos-de-audio")},
                     data={"num_preguntas": "3"}, headers=estudiante)
    assert r.status_code == 200, r.text
    tarea = cliente.get(f"/api/tareas/{r.json()['id']}", headers=estudiante).json()
    assert tarea["estado"] == "listo", tarea
    carpeta = tmp_path / "subidas"
    assert len(list(carpeta.iterdir())) == 1
    cid = tarea["cuestionario_id"]
    detalle = cliente.get(f"/api/cuestionarios/{cid}", headers=estudiante).json()
    assert detalle["medio"] == "audio"
    nombre = detalle["archivo_url"].rsplit("/", 1)[-1]
    assert cliente.get(f"/api/medios/{nombre}").status_code == 200
    assert cliente.delete(f"/api/cuestionarios/{cid}", headers=estudiante).status_code == 204
    assert list(carpeta.iterdir()) == []
    assert cliente.get(f"/api/medios/{nombre}").status_code == 404


def test_subida_con_extension_no_permitida_400(cliente, estudiante):
    r = cliente.post("/api/procesar/archivo", files={"archivo": ("virus.exe", b"x")}, headers=estudiante)
    assert r.status_code == 400


# ---------- Estadísticas ----------

def test_estadisticas_estudiante(cliente, docente, estudiante, crear_cuestionario, intentar):
    cid = _preparar_resultados(cliente, docente, estudiante, crear_cuestionario, intentar)
    e = cliente.get("/api/estadisticas/yo", headers=estudiante).json()
    assert e["rol"] == "estudiante" and e["docente"] is None
    assert e["intentos_finalizados"] == 2
    assert e["promedio_porcentaje"] == 75.0 and e["mejor_porcentaje"] == 100.0
    assert e["cuestionarios_unidos"] == 1 and e["cuestionarios_generados"] == 0
    assert [p["porcentaje"] for p in e["evolucion"]] == [50.0, 100.0]
    assert e["evolucion"][0]["fecha"].endswith(("Z", "+00:00"))
    assert len(e["temas_a_reforzar"]) == 1  # solo falló una pregunta, una vez
    assert e["temas_a_reforzar"][0]["cuestionario_id"] == cid and e["temas_a_reforzar"][0]["fallos"] == 1


def test_estadisticas_docente(cliente, docente, estudiante, crear_cuestionario, intentar):
    cid = _preparar_resultados(cliente, docente, estudiante, crear_cuestionario, intentar)
    d = cliente.get("/api/estadisticas/yo", headers=docente).json()["docente"]
    assert (d["cuestionarios_publicados"], d["estudiantes_unicos"], d["intentos_recibidos"], d["promedio_general"]) == (1, 1, 2, 75.0)
    assert d["por_cuestionario"][0]["id"] == cid and d["por_cuestionario"][0]["intentos"] == 2


def test_estadisticas_vacias(cliente, estudiante):
    e = cliente.get("/api/estadisticas/yo", headers=estudiante).json()
    assert e["intentos_finalizados"] == 0 and e["promedio_porcentaje"] is None
    assert e["evolucion"] == [] and e["temas_a_reforzar"] == []


# ---------- Encuesta SUS ----------

def test_sus_responder_actualizar_y_mia(cliente, estudiante):
    assert cliente.get("/api/sus/mia", headers=estudiante).status_code == 404
    r = cliente.post("/api/sus", json={"respuestas": [3] * 10, "comentario": "  Bien  "}, headers=estudiante)
    assert r.status_code == 200 and r.json()["puntaje"] == 50 and r.json()["interpretacion"] == "Pobre"
    assert r.json()["comentario"] == "Bien"
    r = cliente.post("/api/sus", json={"respuestas": MEJOR}, headers=estudiante)
    assert r.json()["puntaje"] == 100 and r.json()["interpretacion"] == "Excelente"
    mia = cliente.get("/api/sus/mia", headers=estudiante).json()
    assert mia["puntaje"] == 100 and mia["comentario"] is None
    assert cliente.get("/api/sus/resumen", headers=estudiante).status_code == 403


def test_sus_valida_entrada(cliente, estudiante):
    assert cliente.post("/api/sus", json={"respuestas": [3] * 9}, headers=estudiante).status_code == 422
    assert cliente.post("/api/sus", json={"respuestas": [6] + [3] * 9}, headers=estudiante).status_code == 422
    assert cliente.post("/api/sus", json={"respuestas": [3] * 10}).status_code == 401


def test_sus_resumen_solo_docente_y_csv_anonimo(cliente, docente, estudiante, otro_estudiante):
    cliente.post("/api/sus", json={"respuestas": MEJOR}, headers=estudiante)
    cliente.post("/api/sus", json={"respuestas": [3] * 10, "comentario": '=HYPERLINK("x")'}, headers=otro_estudiante)
    assert cliente.get("/api/sus/resumen.csv", headers=estudiante).status_code == 403
    r = cliente.get("/api/sus/resumen", headers=docente).json()
    assert r["n"] == 2 and r["promedio"] == 75.0 and r["minimo"] == 50 and r["maximo"] == 100
    assert r["distribucion"] == {"Pobre": 1, "Aceptable bajo": 0, "Bueno": 0, "Excelente": 1}
    assert len(r["promedio_por_item"]) == 10 and r["promedio_por_item"][0] == 4.0
    csv = cliente.get("/api/sus/resumen.csv", headers=docente)
    assert csv.content.startswith(b"\xef\xbb\xbf")
    texto = csv.content.decode("utf-8-sig")
    assert "prueba.com" not in texto and "Estudiante" not in texto
    assert "'=HYPERLINK" in texto


def test_sus_resumen_vacio(cliente, docente):
    r = cliente.get("/api/sus/resumen", headers=docente).json()
    assert r["n"] == 0 and r["promedio"] is None
