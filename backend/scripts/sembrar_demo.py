r"""Siembra datos de DEMOSTRACIÓN realistas (Sprint 9). Idempotente, sin IA y sin llamadas a internet.

Uso (desde la carpeta backend):
    .\.venv\Scripts\python.exe scripts\sembrar_demo.py              # siembra (solo añade; si ya está sembrado, no hace nada)
    .\.venv\Scripts\python.exe scripts\sembrar_demo.py --reset-demo # borra SOLO lo que creó este script
    .\.venv\Scripts\python.exe scripts\sembrar_demo.py --reset-demo --sembrar   # borra y vuelve a sembrar

Sobre la estructura de `sembrar_estructura.py` (que se ejecuta primero) crea, para el docente demo (periodo 2026-2):
- 3 grupos (Bases de Datos, Estructuras de Datos y Redes de Computadores) y 24 estudiantes ficticios con nombres
  colombianos comunes (correo @demo.com, clave Demo12345, consentimientos aceptados), matriculados;
- 5 cuestionarios publicados (bases de datos relacionales, normalización, ordenamiento, TCP/IP y una versión CONTROL
  del de ordenamiento asignada al grupo de Redes para la comparación), cada uno con 8 preguntas escritas a mano,
  RA, nivel de Bloom, explicaciones, marcas de tiempo y verificación «verificada»;
- intentos de las últimas 6 semanas con perfiles (buenos, medios, en riesgo), repasos diferidos, 2 clases en vivo
  históricas, respuestas abiertas con nota sugerida (algunas aprobadas), 15 respuestas SUS, banco y notificaciones.

Todo lo creado se anota en la tabla `registro_demo`; `--reset-demo` borra únicamente esas filas (y lo que cuelga de ellas).
Los videos son públicos y en español (youtube_id reales, verificados con oEmbed el 2026-10-21). Si alguno deja de estar
disponible, cambia el `youtube_id` en `datos_demo.py` o edita el video desde la plataforma. Las transcripciones son
resúmenes breves escritos para la demo; no son la transcripción literal del video.
"""
import argparse
import json
import math
import random
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import delete, select  # noqa: E402

import datos_demo as D  # noqa: E402
import sembrar_estructura as E  # noqa: E402
from app.db import SessionLocal, crear_tablas  # noqa: E402
from app.modelos import (  # noqa: E402
    AlertaSeguimiento,
    Asignatura,
    Cuestionario,
    Grupo,
    Intento,
    Matricula,
    Notificacion,
    ParticipanteVivo,
    Pregunta,
    PreguntaBanco,
    Programa,
    RegistroDemo,
    Repaso,
    ResultadoAprendizaje,
    RespuestaSUS,
    RespuestaVivo,
    SesionVivo,
    Usuario,
    Video,
    ahora,
    como_utc,
    asignatura_ra,
    generar_codigo,
)
from app.schemas import Segmento, Transcripcion  # noqa: E402
from app.seguridad import hashear_password  # noqa: E402
from app.services.alertas import calcular_alertas  # noqa: E402
from app.services.calificacion import calcular_puntaje, nivel_por_puntaje  # noqa: E402
from app.services.sus import calcular_puntaje as puntaje_sus  # noqa: E402
from app.services.vivo import calcular_puntos  # noqa: E402

CLAVE = E.CLAVE_DEMO
PERIODO = E.PERIODO
SEMILLA = 2026
REPASO_DIAS = 7

# Publicación de cada cuestionario: días atrás
PUBLICADO_HACE = {"relacional": 41, "normalizacion": 27, "ordenamiento": 34, "tcpip": 20, "ordenamiento_control": 22}
# Cuestionarios que hace cada grupo (0 = BD, 1 = ED, 2 = Redes)
QUIZ_DE_GRUPO = {0: ["relacional", "normalizacion"], 1: ["ordenamiento"], 2: ["tcpip", "ordenamiento_control"]}
# Distractor que nadie elige (pregunta 0-based) para que el análisis de ítems muestre un distractor no funcional
SIN_DISTRACTOR = {("relacional", 3), ("ordenamiento", 3), ("tcpip", 4)}


# ---------- utilidades ----------

def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _sigmoide(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def _registrar(db, tabla: str, objeto) -> None:
    db.add(RegistroDemo(entidad=tabla, entidad_id=objeto.id))


def _ids(db, tabla: str) -> list[int]:
    return list(db.scalars(select(RegistroDemo.entidad_id).where(RegistroDemo.entidad == tabla)))


def ya_sembrado(db) -> bool:
    return db.scalar(select(RegistroDemo.id).where(RegistroDemo.entidad == "marca")) is not None


# ---------- reset ----------

def reset(db) -> dict:
    """Borra SOLO lo creado por el script (según `registro_demo`). Devuelve cuántas filas borró por tabla."""
    borrados: dict[str, int] = {}
    usuarios, cuestionarios, grupos = _ids(db, "usuarios"), _ids(db, "cuestionarios"), _ids(db, "grupos")
    sesiones = _ids(db, "sesiones_vivo")

    def quitar(nombre, sentencia):
        borrados[nombre] = db.execute(sentencia).rowcount or 0

    if sesiones:
        quitar("respuestas_vivo", delete(RespuestaVivo).where(RespuestaVivo.sesion_id.in_(sesiones)))
        quitar("participantes_vivo", delete(ParticipanteVivo).where(ParticipanteVivo.sesion_id.in_(sesiones)))
        quitar("sesiones_vivo", delete(SesionVivo).where(SesionVivo.id.in_(sesiones)))
    if cuestionarios or usuarios:
        quitar("repasos", delete(Repaso).where(Repaso.cuestionario_id.in_(cuestionarios) | Repaso.usuario_id.in_(usuarios)))
        quitar("intentos", delete(Intento).where(Intento.cuestionario_id.in_(cuestionarios) | Intento.usuario_id.in_(usuarios)))
    if cuestionarios:
        quitar("preguntas", delete(Pregunta).where(Pregunta.cuestionario_id.in_(cuestionarios)))
    if usuarios:
        quitar("respuestas_sus", delete(RespuestaSUS).where(RespuestaSUS.usuario_id.in_(usuarios)))
        quitar("notificaciones_estudiantes", delete(Notificacion).where(Notificacion.usuario_id.in_(usuarios)))
    ids_notif = _ids(db, "notificaciones")
    if ids_notif:
        quitar("notificaciones_docente", delete(Notificacion).where(Notificacion.id.in_(ids_notif)))
    claves = [f"pub:{c}" for c in cuestionarios] + [f"alerta:{g}:%" for g in grupos]
    for clave in claves:  # notificaciones que la plataforma generó después a partir de lo sembrado
        db.execute(delete(Notificacion).where(Notificacion.clave.like(clave)))
    if grupos:
        quitar("alertas_seguimiento", delete(AlertaSeguimiento).where(AlertaSeguimiento.grupo_id.in_(grupos)))
        quitar("matriculas", delete(Matricula).where(Matricula.grupo_id.in_(grupos) | Matricula.estudiante_id.in_(usuarios)))
    ids_banco = _ids(db, "banco_preguntas")
    if ids_banco:
        quitar("banco_preguntas", delete(PreguntaBanco).where(PreguntaBanco.id.in_(ids_banco)))
    if cuestionarios:
        quitar("cuestionarios", delete(Cuestionario).where(Cuestionario.id.in_(cuestionarios)))
    ids_videos = _ids(db, "videos")
    if ids_videos:
        quitar("videos", delete(Video).where(Video.id.in_(ids_videos)))
    if grupos:
        quitar("grupos", delete(Grupo).where(Grupo.id.in_(grupos)))
    if usuarios:
        quitar("usuarios", delete(Usuario).where(Usuario.id.in_(usuarios)))
    ids_asig = _ids(db, "asignaturas")
    if ids_asig:
        db.execute(delete(asignatura_ra).where(asignatura_ra.c.asignatura_id.in_(ids_asig)))
        quitar("asignaturas", delete(Asignatura).where(Asignatura.id.in_(ids_asig)))
    ids_ra = _ids(db, "resultados_aprendizaje")
    if ids_ra:
        db.execute(delete(asignatura_ra).where(asignatura_ra.c.ra_id.in_(ids_ra)))
        quitar("resultados_aprendizaje", delete(ResultadoAprendizaje).where(ResultadoAprendizaje.id.in_(ids_ra)))
    db.execute(delete(RegistroDemo))
    db.commit()
    return borrados


# ---------- simulación de respuestas ----------

def _aleatorio_normal(rng: random.Random, media: float, desv: float) -> float:
    return rng.gauss(media, desv)


HABILIDAD = {  # (media, desviación) en logits
    "bueno": (1.5, 0.4), "medio": (0.3, 0.4), "bajo": (-1.2, 0.3),
    "inactivo": (0.0, 0.3), "caida": (1.2, 0.3), "vencidos": (-0.1, 0.3),
}


class SimuladorRespuestas:
    def __init__(self, rng: random.Random):
        self.rng = rng

    def _prob(self, habilidad: float, pregunta: tuple) -> float:
        dificultad, discriminacion = pregunta[8], pregunta[9]
        azar = 0.5 if pregunta[0] == "verdadero_falso" else 0.25
        return azar + (1 - azar) * _sigmoide(1.4 * discriminacion * (habilidad - dificultad))

    def respuestas(self, clave: str, preguntas_orm: list, datos: list, habilidad: float, correctas: int | None = None,
                   tier: str | None = None) -> list[dict]:
        """Lista `respuestas_json` de un intento. `correctas` fuerza cuántas cerradas acierta."""
        rng = self.rng
        cerradas = [i for i, d in enumerate(datos) if d[0] != "abierta"]
        aciertos: set[int] = set()
        if correctas is None:
            aciertos = {i for i in cerradas if rng.random() < self._prob(habilidad, datos[i])}
        else:
            ranking = sorted(cerradas, key=lambda i: -(self._prob(habilidad, datos[i]) + rng.random() * 0.3))
            aciertos = set(ranking[:correctas])
        salida = []
        for i, d in enumerate(datos):
            p = preguntas_orm[i]
            if d[0] == "abierta":
                texto, nota, retro, falto = D.QUIZZES[clave.replace("_control", "")]["abierta"][tier or self.nivel_abierta(habilidad)]
                salida.append({
                    "pregunta_id": p.id, "respuesta": texto, "correcta": None,
                    "ia": {"puntaje": nota, "nivel": nivel_por_puntaje(nota), "retroalimentacion": retro, "falto": falto, "proveedor": "demo"},
                })
                continue
            if i in aciertos:
                eleccion = d[3]
            elif d[0] == "verdadero_falso":
                eleccion = "Falso" if d[3] == "Verdadero" else "Verdadero"
            else:
                malas = [o for o in d[2] if o != d[3]]
                pesos = [0.5, 0.3, 0.2]
                if (clave.replace("_control", ""), i) in SIN_DISTRACTOR:
                    pesos = [0.6, 0.4, 0.0]
                eleccion = rng.choices(malas, weights=pesos)[0]
            salida.append({"pregunta_id": p.id, "respuesta": eleccion, "correcta": eleccion == d[3]})
        return salida

    def nivel_abierta(self, habilidad: float) -> str:
        valor = habilidad + self.rng.gauss(0, 0.4)
        return "buena" if valor > 1.0 else "media" if valor > -0.2 else "pobre"


# ---------- siembra ----------

def sembrar(db, ahora_: datetime | None = None, semilla: int = SEMILLA, verboso: bool = True) -> dict:
    """Siembra los datos de demostración. Devuelve un resumen; si ya estaban sembrados no hace nada."""
    log = print if verboso else (lambda *a, **k: None)
    E.sembrar(db)
    if ya_sembrado(db):
        log("Los datos de demostración ya estaban sembrados: no se hizo nada (usa --reset-demo para rehacerlos).")
        return {"sembrado": False}

    rng = random.Random(semilla)
    sim = SimuladorRespuestas(rng)
    ahora_ = ahora_ or ahora()

    def hace(dias: float) -> datetime:
        """Momento de `dias` atrás, con una hora del día de clase (08:00 a 19:00 en Colombia = 13:00 a 24:00 UTC)."""
        base = ahora_ - timedelta(days=int(dias))
        momento = base.replace(hour=13 + rng.randrange(11), minute=rng.randrange(60), second=rng.randrange(60), microsecond=0)
        return min(momento, ahora_ - timedelta(minutes=30))

    docente = db.scalar(select(Usuario).where(Usuario.email == "docente@demo.com"))
    programa = db.scalar(select(Programa).where(Programa.codigo == E.PROGRAMA[1]))
    asig = {a.codigo: a for a in db.scalars(select(Asignatura).where(Asignatura.programa_id == programa.id))}
    ras = {r.codigo: r for r in db.scalars(select(ResultadoAprendizaje).where(ResultadoAprendizaje.programa_id == programa.id))}

    # RA6 y asignatura de Redes (creados por la demo, se registran para poder borrarlos)
    if "RA6" not in ras:
        ra6 = ResultadoAprendizaje(programa_id=programa.id, codigo="RA6",
                                   descripcion="Describe, configura y analiza redes de computadores y sus protocolos (ejemplo).")
        db.add(ra6)
        db.flush()
        _registrar(db, "resultados_aprendizaje", ra6)
        ras["RA6"] = ra6
    if "RD201" not in asig:
        redes = Asignatura(programa_id=programa.id, nombre="Redes de Computadores", codigo="RD201", semestre=6,
                           resultados=[ras["RA6"], ras["RA1"]])
        db.add(redes)
        db.flush()
        _registrar(db, "asignaturas", redes)
        asig["RD201"] = redes

    # Grupos
    grupos = []
    for asignatura, nombre in (("BD101", "Grupo B"), ("ED101", "Grupo A"), ("RD201", "Grupo A")):
        while True:
            codigo = generar_codigo()
            if not db.scalar(select(Grupo.id).where(Grupo.codigo_ingreso == codigo)):
                break
        g = Grupo(asignatura_id=asig[asignatura].id, docente_id=docente.id, periodo=PERIODO, nombre=nombre,
                  codigo_ingreso=codigo, creado_en=hace(46))
        db.add(g)
        db.flush()
        _registrar(db, "grupos", g)
        grupos.append(g)
    log(f"Grupos: {', '.join(g.asignatura.nombre + ' ' + g.nombre for g in grupos)}")

    # Estudiantes
    estudiantes: list[tuple[Usuario, str, int]] = []
    usados = set(db.scalars(select(Usuario.email)))
    for nombre, perfil, gi in D.ESTUDIANTES:
        tokens = _sin_tildes(nombre).lower().split()
        base = f"{tokens[0]}.{tokens[-2]}"
        email, n = f"{base}@demo.com", 1
        while email in usados:
            n += 1
            email = f"{base}{n}@demo.com"
        usados.add(email)
        u = Usuario(nombre=nombre, email=email, password_hash=hashear_password(CLAVE), rol="estudiante",
                    acepta_tratamiento_datos=True, consentimiento_investigacion=True, consentimiento_fecha=hace(45),
                    creado_en=hace(45))
        db.add(u)
        db.flush()
        _registrar(db, "usuarios", u)
        db.add(Matricula(grupo_id=grupos[gi].id, estudiante_id=u.id, creado_en=hace(44)))
        estudiantes.append((u, perfil, gi))
    log(f"Estudiantes creados: {len(estudiantes)} (clave {CLAVE})")

    # Videos, cuestionarios y preguntas
    cuestionarios: dict[str, Cuestionario] = {}
    preguntas: dict[str, list[Pregunta]] = {}
    datos_preguntas: dict[str, list[tuple]] = {}
    grupo_de_quiz = {q: gi for gi, qs in QUIZ_DE_GRUPO.items() for q in qs}
    for clave in PUBLICADO_HACE:
        contenido = D.QUIZZES[clave.replace("_control", "")]
        control = clave.endswith("_control")
        yt = contenido["video"]["youtube_id"]
        video = db.scalar(select(Video).where(Video.youtube_id == yt))
        if video is None:
            trans = Transcripcion(fuente="subtitulos_youtube", idioma="es",
                                  segmentos=[Segmento(inicio=s, texto=t) for s, t in contenido["transcripcion"]])
            video = Video(youtube_id=yt, url=f"https://www.youtube.com/watch?v={yt}", titulo_original=contenido["video"]["titulo"],
                          fuente_transcripcion="subtitulos_youtube", transcripcion_json=trans.model_dump_json(),
                          plataforma="youtube", video_externo_id=yt, creado_en=hace(PUBLICADO_HACE[clave] + 2))
            db.add(video)
            db.flush()
            _registrar(db, "videos", video)
        publicado = hace(PUBLICADO_HACE[clave])
        c = Cuestionario(
            video_id=video.id, creador_id=docente.id,
            titulo=contenido["titulo"] + (" (versión control)" if control else ""),
            resumen=contenido["resumen"], ideas_clave_json=json.dumps(contenido["ideas_clave"], ensure_ascii=False),
            proveedor_ia="demo", num_preguntas=len(contenido["preguntas"]), publicado=True,
            modo="control" if control else "aprendizaje", repaso_dias=REPASO_DIAS,
            segundos_generacion=rng.randrange(70, 130), segundos_edicion=rng.randrange(420, 1500),
            publicado_en=publicado, creado_en=publicado - timedelta(days=1), estimacion_manual_min=90,
            grupo_id=grupos[grupo_de_quiz[clave]].id,
        )
        db.add(c)
        db.flush()
        _registrar(db, "cuestionarios", c)
        lista = []
        for orden, d in enumerate(contenido["preguntas"]):
            tipo, enunciado, opciones, correcta, explicacion, marca, ra, bloom = d[:8]
            seg = max((s for s in contenido["transcripcion"] if s[0] <= int(marca[:2]) * 60 + int(marca[3:])), key=lambda s: s[0])
            verificacion = {"estado": "verificada", "respaldo": "si", "cita": seg[1][:220], "marca_tiempo": marca,
                            "inequivoca": True, "problemas": [], "proveedor": "demo"}
            p = Pregunta(cuestionario_id=c.id, orden=orden, tipo=tipo, enunciado=enunciado,
                         opciones_json=json.dumps(opciones, ensure_ascii=False), respuesta_correcta=correcta,
                         explicacion=explicacion, marca_tiempo=marca, ra_id=ras[ra].id, nivel_bloom=bloom,
                         verificacion=json.dumps(verificacion, ensure_ascii=False))
            db.add(p)
            lista.append(p)
        db.flush()
        cuestionarios[clave], preguntas[clave], datos_preguntas[clave] = c, lista, contenido["preguntas"]
    log(f"Cuestionarios: {len(cuestionarios)} (8 preguntas cada uno)")

    # Intentos y repasos
    def crear_intento(u, clave, tipo, momento, habilidad, correctas=None, tier=None, aprobar=True) -> Intento:
        resp = sim.respuestas(clave, preguntas[clave], datos_preguntas[clave], habilidad, correctas, tier)
        if aprobar:  # el docente aprueba (a veces ajusta) algunas notas sugeridas de abiertas
            for r in resp:
                if r.get("ia") and rng.random() < 0.55:
                    r["nota_final"] = max(0, min(100, r["ia"]["puntaje"] + rng.choice([0, 0, 0, 5, -5])))
                    r["calificada_por"] = docente.id
        puntaje, total = calcular_puntaje(resp, preguntas[clave])
        i = Intento(usuario_id=u.id, cuestionario_id=cuestionarios[clave].id, puntaje=puntaje, total=total,
                    respuestas_json=json.dumps(resp, ensure_ascii=False), finalizado=True, tipo=tipo, creado_en=momento)
        db.add(i)
        db.flush()
        return i

    n_intentos = 0
    for u, perfil, gi in estudiantes:
        media, desv = HABILIDAD[perfil]
        habilidad = rng.gauss(media, desv)
        quizzes = QUIZ_DE_GRUPO[gi]
        if perfil == "inactivo":
            quizzes = quizzes[:1]
        ultimo_inicial: Intento | None = None
        for k, clave in enumerate(quizzes):
            pub = PUBLICADO_HACE[clave]
            control = clave.endswith("_control")
            correctas = None
            if perfil == "caida":
                correctas = 7 if k == 0 else 3
            dia_inicial = pub - rng.uniform(0.5, 3 if perfil == "inactivo" else 5)
            inicial = crear_intento(u, clave, "inicial", hace(dia_inicial), habilidad + rng.gauss(0, 0.15), correctas)
            n_intentos += 1
            ultimo_inicial = inicial
            # repaso diferido: se completa según el perfil
            prob = {"bueno": 0.92, "medio": 0.65, "caida": 1.0 if k == 0 else 0.0}.get(perfil, 0.0)
            repaso = Repaso(usuario_id=u.id, cuestionario_id=cuestionarios[clave].id,
                            disponible_desde=inicial.creado_en + timedelta(days=REPASO_DIAS))
            db.add(repaso)
            db.flush()
            dia_dif = dia_inicial - REPASO_DIAS - rng.uniform(0.2, 3)
            if rng.random() < prob and dia_dif > 0.6:
                delta = -1.2 if control else 0.1  # sin retroalimentación se retiene menos
                dif = crear_intento(u, clave, "diferido", hace(dia_dif), habilidad + delta + rng.gauss(0, 0.2))
                repaso.completado_intento_id = dif.id
                n_intentos += 1
        # práctica reciente: todos los activos (buenos y medios) practican en los últimos días y no empeoran bruscamente
        clave_final = quizzes[-1]
        if perfil == "caida" and len(quizzes) == 1:
            crear_intento(u, clave_final, "practica", hace(rng.uniform(2, 6)), habilidad, correctas=3)
            n_intentos += 1
        elif perfil in ("bueno", "medio"):
            clave_practica = next(q for q in reversed(quizzes) if not q.endswith("_control"))
            previos = list(db.scalars(select(Intento).where(Intento.usuario_id == u.id).order_by(Intento.creado_en, Intento.id)))
            previo = previos[-1]
            cerradas_previas = sum(1 for r in json.loads(previo.respuestas_json) if r.get("correcta") is True)
            practica = crear_intento(u, clave_practica, "practica", hace(rng.uniform(0.7, 12)), habilidad + 0.5)
            aciertos = sum(1 for r in json.loads(practica.respuestas_json) if r.get("correcta") is True)
            if aciertos < cerradas_previas - 1:  # evita una caída artificial (las caídas del perfil «caida» son deliberadas)
                db.delete(practica)
                db.flush()
                crear_intento(u, clave_practica, "practica", practica.creado_en, habilidad + 0.5, correctas=min(7, cerradas_previas))
            n_intentos += 1
    log(f"Intentos creados: {n_intentos}")

    # Clases en vivo históricas
    def sesion_vivo(clave: str, gi: int, dias: float) -> SesionVivo:
        c, datos = cuestionarios[clave], datos_preguntas[clave]
        inicio = hace(dias)
        pines = set(db.scalars(select(SesionVivo.pin)))
        pin = next(p for p in (str(rng.randrange(100000, 999999)) for _ in range(50)) if p not in pines)
        s = SesionVivo(cuestionario_id=c.id, docente_id=docente.id, pin=pin, estado="finalizada",
                       pregunta_actual=len(datos) - 1, segundos_por_pregunta=30, creada_en=inicio,
                       actividad_en=inicio + timedelta(minutes=24), finalizada_en=inicio + timedelta(minutes=25))
        db.add(s)
        db.flush()
        _registrar(db, "sesiones_vivo", s)
        miembros = [(u, perfil) for u, perfil, g in estudiantes if g == gi and perfil != "inactivo"]
        apodos = [(u.nombre.split()[0][:12], u, perfil) for u, perfil in miembros]
        apodos += [("Invitado1", None, "medio"), ("Invitado2", None, "bajo")]
        for apodo, u, perfil in apodos:
            habilidad = rng.gauss(*HABILIDAD[perfil])
            part = ParticipanteVivo(sesion_id=s.id, apodo=apodo, usuario_id=u.id if u else None, creado_en=inicio)
            db.add(part)
            db.flush()
            total = 0
            for p, d in zip(preguntas[clave], datos):
                if d[0] == "abierta":
                    texto = D.QUIZZES[clave]["abierta"][sim.nivel_abierta(habilidad)][0]
                    db.add(RespuestaVivo(sesion_id=s.id, participante_id=part.id, pregunta_id=p.id, respuesta=texto,
                                         correcta=None, ms_respuesta=rng.randrange(8000, 28000), puntos=0))
                    continue
                correcta = rng.random() < sim._prob(habilidad, d)
                ms = rng.randrange(2500, 26000)
                puntos = calcular_puntos(correcta, ms, 30)
                total += puntos
                eleccion = d[3] if correcta else next(o for o in (d[2] or ["Verdadero", "Falso"]) if o != d[3])
                db.add(RespuestaVivo(sesion_id=s.id, participante_id=part.id, pregunta_id=p.id, respuesta=eleccion,
                                     correcta=correcta, ms_respuesta=ms, puntos=puntos))
            part.puntaje = total
        return s

    sesion_vivo("relacional", 0, 18)
    sesion_vivo("ordenamiento", 1, 9)
    log("Clases en vivo históricas: 2")

    # Encuesta SUS (15 respuestas, promedio cercano a 75)
    candidatos = [u for u, _, _ in estudiantes]
    rng.shuffle(candidatos)
    puntajes = []
    for idx, u in enumerate(candidatos[:15]):
        resp = []
        for numero in range(1, 11):
            valor = rng.gauss(4.05, 0.8) if numero % 2 == 1 else rng.gauss(1.95, 0.8)
            resp.append(max(1, min(5, round(valor))))
        puntaje = puntaje_sus(resp)
        puntajes.append(puntaje)
        db.add(RespuestaSUS(usuario_id=u.id, respuestas_json=json.dumps(resp), puntaje_sus=puntaje,
                            comentario=D.COMENTARIOS_SUS[idx] if idx < len(D.COMENTARIOS_SUS) else None, creado_en=hace(rng.uniform(1, 25))))
    log(f"Encuestas SUS: 15 (promedio {sum(puntajes) / len(puntajes):.1f})")

    # Banco de preguntas
    n_banco = 0
    for clave, c in cuestionarios.items():
        if clave.endswith("_control"):
            continue
        for idx in (0, 4, 6):
            d = datos_preguntas[clave][idx]
            ra = ras[d[6]]
            b = PreguntaBanco(autor_id=docente.id, visibilidad="institucional", tipo=d[0], enunciado=d[1],
                              opciones_json=json.dumps(d[2], ensure_ascii=False), respuesta_correcta=d[3], explicacion=d[4],
                              nivel_bloom=d[7], ra_codigo=ra.codigo, ra_descripcion=ra.descripcion,
                              asignatura_nombre=c.grupo.asignatura.nombre if c.grupo else None,
                              etiquetas_json=json.dumps(D.BANCO_ETIQUETAS[clave], ensure_ascii=False),
                              verificacion=preguntas[clave][idx].verificacion, creado_en=hace(rng.uniform(3, 30)))
            db.add(b)
            db.flush()
            _registrar(db, "banco_preguntas", b)
            n_banco += 1
    log(f"Preguntas en el banco: {n_banco}")

    # Atención de una alerta (se registra con los motivos que tenga hoy el estudiante «inactivo» del grupo ED)
    db.flush()
    por_est = {a.estudiante_id: a for a in calcular_alertas(db, grupos, hoy=ahora_)}
    daniel = next(u for u, perfil, gi in estudiantes if perfil == "inactivo" and gi == 1)
    if daniel.id in por_est:
        a = por_est[daniel.id]
        db.add(AlertaSeguimiento(grupo_id=a.grupo_id, estudiante_id=daniel.id, atendido_por_id=docente.id,
                                 motivos=",".join(m.codigo for m in a.motivos),
                                 nota="Hablé con él: tuvo problemas de conectividad; se compromete a ponerse al día.", creado_en=hace(3)))

    # Notificaciones
    for u, perfil, gi in estudiantes:
        for clave in QUIZ_DE_GRUPO[gi]:
            c = cuestionarios[clave]
            db.add(Notificacion(usuario_id=u.id, tipo="publicado", titulo="Nuevo cuestionario publicado",
                                mensaje=f"«{c.titulo}» está disponible en {grupos[gi].nombre}.", enlace=f"/cuestionarios/{c.id}",
                                leida=PUBLICADO_HACE[clave] > 10 or rng.random() < 0.5, clave=f"pub:{c.id}", creada_en=c.publicado_en))
    for r in db.scalars(select(Repaso).where(Repaso.completado_intento_id.is_(None), Repaso.cuestionario_id.in_([c.id for c in cuestionarios.values()]))):
        if como_utc(r.disponible_desde) > ahora_:
            continue
        c = db.get(Cuestionario, r.cuestionario_id)
        db.add(Notificacion(usuario_id=r.usuario_id, tipo="repaso", titulo="Repaso disponible",
                            mensaje=f"Ya puedes hacer el repaso de «{c.titulo}».", enlace=f"/cuestionarios/{c.id}",
                            leida=False, clave=f"repaso:{r.id}", creada_en=min(como_utc(r.disponible_desde), ahora_ - timedelta(hours=2))))
    visibles = calcular_alertas(db, grupos, hoy=ahora_)
    for k, (titulo, mensaje, dias) in enumerate([
        ("Estudiantes que necesitan atención", f"{len(visibles)} estudiantes tienen alertas activas en tus grupos.", 0.2),
        ("Clase en vivo finalizada", "«Algoritmos de ordenamiento»: 10 participantes, resultados disponibles en el historial.", 9),
        ("Clase en vivo finalizada", "«Bases de datos relacionales»: 11 participantes, resultados disponibles en el historial.", 18),
    ]):
        n = Notificacion(usuario_id=docente.id, tipo="alerta" if k == 0 else "clase_vivo", titulo=titulo, mensaje=mensaje,
                         enlace="/coordinacion" if k == 0 else "/cuestionarios", leida=k > 0, clave=f"demo:{k}", creada_en=hace(dias))
        db.add(n)
        db.flush()
        _registrar(db, "notificaciones", n)

    db.add(RegistroDemo(entidad="marca", entidad_id=1))
    db.commit()
    resumen = {"sembrado": True, "estudiantes": len(estudiantes), "cuestionarios": len(cuestionarios), "intentos": n_intentos,
               "alertas": len(visibles), "sus_promedio": round(sum(puntajes) / len(puntajes), 1)}
    log(f"Listo. Alertas activas: {len(visibles)}. Entra como docente@demo.com / {CLAVE}, coordinador@demo.com o estudiante demo.")
    return resumen


def main() -> None:
    ap = argparse.ArgumentParser(description="Siembra (o borra) los datos de demostración.")
    ap.add_argument("--reset-demo", action="store_true", help="Borra SOLO lo creado por este script.")
    ap.add_argument("--sembrar", action="store_true", help="Con --reset-demo: vuelve a sembrar después de borrar.")
    args = ap.parse_args()
    crear_tablas()
    with SessionLocal() as db:
        if args.reset_demo:
            borrados = reset(db)
            print("Borrado:", ", ".join(f"{k}={v}" for k, v in borrados.items()) or "nada que borrar")
            if not args.sembrar:
                return
        sembrar(db)


if __name__ == "__main__":
    main()
