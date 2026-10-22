"""Clase en vivo (estilo Kahoot): estado en memoria, temporizador del servidor y difusión por WebSocket.

El estado de cada sesión activa vive en memoria (`SesionMem`, con un lock) y se persiste en la BD en cada
transición, al unirse un participante y al recibir cada respuesta. Si el servidor se reinicia, la sesión se
reconstruye desde la BD al primer acceso. Todo el código asíncrono corre en el bucle de eventos de FastAPI y las
secciones que mutan el estado no tienen `await`, por lo que son atómicas.

Las respuestas correctas NUNCA se incluyen en un snapshot mientras la pregunta está abierta.
"""
import asyncio
import json
import logging
import re
import secrets
import threading
import time
import unicodedata
from datetime import datetime, timedelta, timezone

from fastapi import WebSocket
from sqlalchemy import select

from app.db import SessionLocal
from app.modelos import (
    Cuestionario,
    ParticipanteVivo,
    RespuestaVivo,
    SesionVivo,
    Usuario,
    ahora,
    como_utc,
)
from app.services.notificaciones import notificar

log = logging.getLogger(__name__)

MAX_PARTICIPANTES = 200
EXPIRA_INACTIVA_S = 2 * 3600
RETENER_FINALIZADA_S = 30 * 60
PUNTOS_BASE = 500
PUNTOS_TIEMPO = 500
GRACIA_MS = 1500  # margen por la latencia de red al aceptar una respuesta


class ErrorVivo(Exception):
    """Error de negocio con código HTTP asociado."""

    def __init__(self, mensaje: str, codigo: int = 409):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


# ---------- Utilidades puras ----------

def normalizar(texto: str) -> str:
    return " ".join(texto.strip().lower().split())


def calcular_puntos(correcta: bool | None, ms: int, segundos_total: int) -> int:
    """Estilo Kahoot: correcta = 500 + 500 × (tiempo restante / tiempo total); incorrecta o abierta = 0."""
    if not correcta:
        return 0
    total_ms = max(1, segundos_total * 1000)
    restante = max(0, min(total_ms, total_ms - ms))
    return round(PUNTOS_BASE + PUNTOS_TIEMPO * restante / total_ms)


_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})
_SUBCADENAS = (
    "puta", "puto", "mierda", "cabron", "cabrona", "pendejo", "pendeja", "gonorrea", "hijueputa", "hijoputa",
    "malparido", "marica", "maricon", "verga", "carajo", "chingar", "chingada", "follar",
    "fuck", "shit", "bitch", "cunt", "nigger", "nigga", "faggot", "whore", "asshole", "bastard", "nazi", "hitler",
    "porno", "violador", "zorra", "imbecil", "idiota",
)
_PALABRAS = {"pene", "culo", "hdp", "mrd", "ptm", "sexo", "dick", "cock", "ass", "pija", "vagina", "tetas"}


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def es_ofensivo(apodo: str) -> bool:
    """Filtro básico: ignora tildes, mayúsculas, sustituciones tipo «p0rn0» y separadores («p u t a»)."""
    base = _sin_tildes(apodo.lower()).translate(_LEET)
    compacto = re.sub(r"[^a-z]", "", base)
    if any(mal in compacto for mal in _SUBCADENAS):
        return True
    palabras = set(re.findall(r"[a-z]+", base))
    return bool(palabras & _PALABRAS) or compacto in _PALABRAS


def validar_apodo(apodo: str) -> str:
    limpio = " ".join(apodo.split())
    if not 2 <= len(limpio) <= 20:
        raise ErrorVivo("El apodo debe tener entre 2 y 20 caracteres.", 422)
    if es_ofensivo(limpio):
        raise ErrorVivo("Ese apodo no está permitido. Elige otro.", 422)
    return limpio


# ---------- Estado en memoria ----------

class SesionMem:
    def __init__(self, s: SesionVivo, titulo: str, preguntas: list[dict]):
        self.id = s.id
        self.pin = s.pin
        self.docente_id = s.docente_id
        self.cuestionario_id = s.cuestionario_id
        self.titulo = titulo
        self.preguntas = preguntas
        self.segundos = s.segundos_por_pregunta
        self.estado = s.estado
        self.idx = s.pregunta_actual
        self.inicio: float | None = como_utc(s.inicio_pregunta).timestamp() if s.inicio_pregunta else None
        self.actividad = como_utc(s.actividad_en).timestamp()
        self.finalizada_en: float | None = como_utc(s.finalizada_en).timestamp() if s.finalizada_en else None
        self.apodos: dict[int, str] = {}
        self.usuarios: dict[int, int | None] = {}
        self.tokens: dict[str, int] = {}
        self.puntajes: dict[int, int] = {}
        self.actual: dict[int, dict] = {}  # respuestas a la pregunta abierta/actual
        self.cierre: dict | None = None
        self.conexiones: dict[WebSocket, tuple[str, int | None]] = {}
        self.timer: asyncio.Task | None = None
        self.lock = threading.RLock()

    @property
    def pregunta(self) -> dict | None:
        return self.preguntas[self.idx] if 0 <= self.idx < len(self.preguntas) else None


_sesiones: dict[str, SesionMem] = {}
_registro_lock = threading.RLock()


def _dt(epoch: float) -> datetime:
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


def _preguntas_de(c: Cuestionario) -> list[dict]:
    return [
        {"id": p.id, "tipo": p.tipo, "enunciado": p.enunciado, "opciones": json.loads(p.opciones_json or "[]"),
         "correcta": p.respuesta_correcta, "explicacion": p.explicacion}
        for p in c.preguntas
    ]


def _cargar(db, s: SesionVivo) -> SesionMem:
    c = db.get(Cuestionario, s.cuestionario_id)
    m = SesionMem(s, c.titulo, _preguntas_de(c))
    for p in db.scalars(select(ParticipanteVivo).where(ParticipanteVivo.sesion_id == s.id).order_by(ParticipanteVivo.id)):
        m.apodos[p.id] = p.apodo
        m.usuarios[p.id] = p.usuario_id
        m.tokens[p.token] = p.id
        m.puntajes[p.id] = p.puntaje
    pregunta = m.pregunta
    if pregunta is not None:
        for r in db.scalars(select(RespuestaVivo).where(RespuestaVivo.sesion_id == s.id, RespuestaVivo.pregunta_id == pregunta["id"])):
            m.actual[r.participante_id] = {"respuesta": r.respuesta, "correcta": r.correcta, "puntos": r.puntos, "ms": r.ms_respuesta}
    if m.estado in ("resultados_pregunta", "finalizada") and pregunta is not None:
        m.cierre = _calcular_cierre(m)
    return m


def _persistir(m: SesionMem, finalizada: bool = False) -> None:
    with SessionLocal() as db:
        s = db.get(SesionVivo, m.id)
        if s is None:
            return
        s.estado = m.estado
        s.pregunta_actual = m.idx
        s.inicio_pregunta = None if m.inicio is None else _dt(m.inicio)
        s.actividad_en = ahora()
        if finalizada:
            s.finalizada_en = ahora()
        db.commit()


def obtener(pin: str) -> SesionMem | None:
    """Sesión por PIN: de memoria o reconstruida desde la BD. Cierra las abandonadas (2 h sin actividad)."""
    with _registro_lock:
        m = _sesiones.get(pin)
        if m is not None:
            if m.estado != "finalizada" and time.time() - m.actividad > EXPIRA_INACTIVA_S:
                _finalizar_sync(m)
            return m
        with SessionLocal() as db:
            s = db.scalar(select(SesionVivo).where(SesionVivo.pin == pin, SesionVivo.estado != "finalizada"))
            if s is None:
                return None
            if ahora() - como_utc(s.actividad_en) > timedelta(seconds=EXPIRA_INACTIVA_S):
                s.estado = "finalizada"
                s.finalizada_en = ahora()
                db.commit()
                return None
            m = _cargar(db, s)
        _sesiones[pin] = m
    _reanudar_timer(m)
    return m


def obtener_por_id(sesion_id: int) -> SesionMem | None:
    with _registro_lock:
        for m in _sesiones.values():
            if m.id == sesion_id:
                return obtener(m.pin)
    with SessionLocal() as db:
        s = db.get(SesionVivo, sesion_id)
        pin = s.pin if s is not None and s.estado != "finalizada" else None
    return obtener(pin) if pin else None


def _pin_libre(db) -> str:
    for _ in range(200):
        pin = f"{secrets.randbelow(900000) + 100000}"
        if pin in _sesiones:
            continue
        if db.scalar(select(SesionVivo.id).where(SesionVivo.pin == pin, SesionVivo.estado != "finalizada")) is None:
            return pin
    raise ErrorVivo("No se pudo generar un PIN libre. Inténtalo de nuevo.", 503)


def crear_sesion(c: Cuestionario, docente: Usuario, segundos: int) -> SesionMem:
    if not c.preguntas:
        raise ErrorVivo("El cuestionario no tiene preguntas.", 422)
    with SessionLocal() as db:
        s = SesionVivo(cuestionario_id=c.id, docente_id=docente.id, pin=_pin_libre(db), segundos_por_pregunta=segundos)
        db.add(s)
        db.commit()
        db.refresh(s)
        m = SesionMem(s, c.titulo, _preguntas_de(c))
    with _registro_lock:
        _sesiones[m.pin] = m
    return m


def unirse(m: SesionMem, apodo: str, usuario: Usuario | None) -> ParticipanteVivo:
    """Registra un participante (síncrono). Un usuario con cuenta que ya está en la sesión recupera su lugar."""
    if m.estado == "finalizada":
        raise ErrorVivo("Esta clase en vivo ya terminó.", 410)
    with m.lock:
        if usuario is not None:
            for pid, uid in m.usuarios.items():
                if uid == usuario.id:
                    with SessionLocal() as db:
                        return db.get(ParticipanteVivo, pid)
        apodo = validar_apodo(apodo)
        if any(normalizar(a) == normalizar(apodo) for a in m.apodos.values()):
            raise ErrorVivo("Ese apodo ya está en uso en esta sesión. Elige otro.", 409)
        if len(m.apodos) >= MAX_PARTICIPANTES:
            raise ErrorVivo(f"La sesión está llena (máximo {MAX_PARTICIPANTES} participantes).", 409)
        with SessionLocal() as db:
            p = ParticipanteVivo(sesion_id=m.id, apodo=apodo, usuario_id=usuario.id if usuario else None)
            db.add(p)
            db.commit()
            db.refresh(p)
        m.apodos[p.id] = p.apodo
        m.usuarios[p.id] = p.usuario_id
        m.tokens[p.token] = p.id
        m.puntajes[p.id] = 0
        m.actividad = time.time()
        return p


# ---------- Snapshots ----------

def _ranking(m: SesionMem) -> list[tuple[int, int]]:
    return sorted(m.puntajes.items(), key=lambda kv: (-kv[1], m.apodos[kv[0]].lower()))


def _posicion(m: SesionMem, pid: int) -> int:
    mio = m.puntajes.get(pid, 0)
    return 1 + sum(1 for v in m.puntajes.values() if v > mio)


def _top(m: SesionMem, n: int = 5) -> list[dict]:
    return [{"apodo": m.apodos[pid], "puntos": pts, "posicion": _posicion(m, pid)} for pid, pts in _ranking(m)[:n]]


def _calcular_cierre(m: SesionMem) -> dict:
    p = m.pregunta
    abierta = p["tipo"] == "abierta"
    distribucion = []
    if not abierta:
        cuenta = {normalizar(o): 0 for o in p["opciones"]}
        for r in m.actual.values():
            k = normalizar(r["respuesta"])
            if k in cuenta:
                cuenta[k] += 1
        distribucion = [
            {"opcion": o, "cantidad": cuenta[normalizar(o)], "correcta": normalizar(o) == normalizar(p["correcta"])}
            for o in p["opciones"]
        ]
    return {
        "distribucion": distribucion,
        "correcta": None if abierta else p["correcta"],
        "explicacion": p.get("explicacion") or "",
        "respondieron": len(m.actual),
        "abiertas": [r["respuesta"] for r in m.actual.values()] if abierta else [],
    }


def _base(m: SesionMem, rol: str) -> dict:
    pregunta = m.pregunta
    restante = 0
    if m.estado == "pregunta" and m.inicio is not None:
        restante = max(0, int(m.segundos * 1000 - (time.time() - m.inicio) * 1000))
    snap: dict = {
        "tipo": "estado",
        "pin": m.pin,
        "titulo": m.titulo,
        "estado": m.estado,
        "indice": m.idx,
        "total_preguntas": len(m.preguntas),
        "segundos": m.segundos,
        "restante_ms": restante,
        "num_participantes": len(m.apodos),
        "participantes": list(m.apodos.values()),
        "respondieron": len(m.actual) if m.estado == "pregunta" else 0,
        "pregunta": None,
        "resultados": None,
        "ranking": [],
    }
    if pregunta is not None and m.estado in ("pregunta", "resultados_pregunta"):
        snap["pregunta"] = {"id": pregunta["id"], "tipo": pregunta["tipo"], "enunciado": pregunta["enunciado"],
                            "opciones": pregunta["opciones"]}  # sin la respuesta correcta
    if m.estado == "resultados_pregunta" and m.cierre is not None:
        cierre = dict(m.cierre)
        if rol != "presentador":
            cierre["abiertas"] = []
        snap["resultados"] = cierre
        snap["ranking"] = _top(m)
    if m.estado == "finalizada":
        snap["ranking"] = _top(m)
    return snap


def snapshot(m: SesionMem, rol: str, pid: int | None = None, base: dict | None = None) -> dict:
    snap = dict(base) if base is not None else _base(m, rol)
    snap["rol"] = rol
    if rol == "participante" and pid is not None and pid in m.apodos:
        r = m.actual.get(pid)
        yo = {"apodo": m.apodos[pid], "puntos": m.puntajes.get(pid, 0), "posicion": _posicion(m, pid),
              "respondio": r is not None, "mi_respuesta": r["respuesta"] if r else None,
              "correcta": None, "puntos_ganados": None}
        if r is not None and m.estado in ("resultados_pregunta", "finalizada"):
            yo["correcta"] = r["correcta"]
            yo["puntos_ganados"] = r["puntos"]
        snap["yo"] = yo
    return snap


# ---------- Difusión ----------

async def difundir(m: SesionMem, solo_presentador: bool = False) -> None:
    bases: dict[str, dict] = {}
    caidos = []
    for ws, (rol, pid) in list(m.conexiones.items()):
        if solo_presentador and rol != "presentador":
            continue
        base = bases.setdefault(rol, _base(m, rol))
        try:
            await ws.send_json(snapshot(m, rol, pid, base))
        except Exception:  # noqa: BLE001 - conexión rota
            caidos.append(ws)
    for ws in caidos:
        m.conexiones.pop(ws, None)


async def enviar(m: SesionMem, ws: WebSocket) -> None:
    rol, pid = m.conexiones.get(ws, ("participante", None))
    await ws.send_json(snapshot(m, rol, pid))


# ---------- Transiciones ----------

def _cancelar_timer(m: SesionMem) -> None:
    if m.timer is not None and m.timer is not asyncio.current_task():
        m.timer.cancel()
    m.timer = None


async def _esperar_y_cerrar(m: SesionMem, idx: int, espera: float) -> None:
    try:
        await asyncio.sleep(max(0.0, espera))
    except asyncio.CancelledError:
        return
    if m.estado == "pregunta" and m.idx == idx:
        m.timer = None
        await cerrar_pregunta(m)


def _programar_timer(m: SesionMem, espera: float) -> None:
    _cancelar_timer(m)
    m.timer = asyncio.get_running_loop().create_task(_esperar_y_cerrar(m, m.idx, espera))


def _reanudar_timer(m: SesionMem) -> None:
    """Tras reconstruir una sesión desde la BD con una pregunta abierta, retoma el temporizador."""
    if m.estado != "pregunta" or m.inicio is None:
        return
    try:
        _programar_timer(m, m.segundos - (time.time() - m.inicio))
    except RuntimeError:  # sin bucle de eventos (llamada síncrona)
        pass


async def abrir_pregunta(m: SesionMem, idx: int) -> None:
    with m.lock:
        m.idx = idx
        m.estado = "pregunta"
        m.inicio = time.time()
        m.actividad = m.inicio
        m.actual = {}
        m.cierre = None
    _persistir(m)
    _programar_timer(m, m.segundos)
    await difundir(m)


async def cerrar_pregunta(m: SesionMem) -> None:
    with m.lock:
        if m.estado != "pregunta":
            return
        m.estado = "resultados_pregunta"
        m.cierre = _calcular_cierre(m)
        m.actividad = time.time()
    _cancelar_timer(m)
    _persistir(m)
    await difundir(m)


def _finalizar_sync(m: SesionMem) -> None:
    with m.lock:
        if m.estado == "finalizada":
            return
        m.estado = "finalizada"
        m.finalizada_en = time.time()
        m.actividad = m.finalizada_en
        if m.cierre is None and m.pregunta is not None:
            m.cierre = _calcular_cierre(m)
    if m.timer is not None and m.timer is not asyncio.current_task():
        m.timer.cancel()
    m.timer = None
    _persistir(m, finalizada=True)
    # Resultado para los participantes con cuenta
    with SessionLocal() as db:
        for pid, uid in m.usuarios.items():
            if uid:
                notificar(db, uid, "clase_vivo", f"Resultado de la clase en vivo: {m.titulo}",
                          f"Quedaste en el puesto {_posicion(m, pid)} de {len(m.apodos)} con {m.puntajes.get(pid, 0)} puntos.",
                          "/notificaciones", clave=f"vivo:{m.id}")
        db.commit()


async def finalizar(m: SesionMem) -> None:
    _finalizar_sync(m)
    await difundir(m)


async def accion_presentador(m: SesionMem, accion: str) -> None:
    if m.estado == "finalizada":
        raise ErrorVivo("La sesión ya finalizó.")
    if accion == "finalizar":
        await finalizar(m)
    elif accion == "iniciar":
        if m.estado != "lobby":
            raise ErrorVivo("La clase ya comenzó.")
        await abrir_pregunta(m, 0)
    elif accion in ("siguiente", "saltar"):
        if m.estado == "lobby":
            await abrir_pregunta(m, 0)
        elif m.estado == "pregunta":
            await cerrar_pregunta(m)
        elif m.idx + 1 < len(m.preguntas):
            await abrir_pregunta(m, m.idx + 1)
        else:
            await finalizar(m)
    else:
        raise ErrorVivo("Acción no reconocida.", 422)


async def responder(m: SesionMem, pid: int, respuesta: str) -> None:
    ahora_ = time.time()
    with m.lock:
        p = m.pregunta
        if m.estado != "pregunta" or p is None or m.inicio is None:
            raise ErrorVivo("No hay una pregunta abierta.")
        ms = int((ahora_ - m.inicio) * 1000)
        if ms > m.segundos * 1000 + GRACIA_MS:
            raise ErrorVivo("Se acabó el tiempo.")
        if pid in m.actual:
            raise ErrorVivo("Ya respondiste esta pregunta.")
        respuesta = respuesta.strip()
        if not respuesta:
            raise ErrorVivo("La respuesta está vacía.", 422)
        if p["tipo"] == "abierta":
            correcta = None
            respuesta = respuesta[:500]
        else:
            if normalizar(respuesta) not in {normalizar(o) for o in p["opciones"]}:
                raise ErrorVivo("Esa opción no existe.", 422)
            correcta = normalizar(respuesta) == normalizar(p["correcta"])
        puntos = calcular_puntos(correcta, ms, m.segundos)
        m.actual[pid] = {"respuesta": respuesta, "correcta": correcta, "puntos": puntos, "ms": ms}
        m.puntajes[pid] = m.puntajes.get(pid, 0) + puntos
        m.actividad = ahora_
        total = m.puntajes[pid]
    with SessionLocal() as db:
        db.add(RespuestaVivo(sesion_id=m.id, participante_id=pid, pregunta_id=p["id"], respuesta=respuesta,
                             correcta=correcta, ms_respuesta=ms, puntos=puntos))
        part = db.get(ParticipanteVivo, pid)
        if part is not None:
            part.puntaje = total
        db.commit()
    # Confirmación al participante (sin revelar si acertó) y conteo en vivo al presentador
    await difundir(m, solo_presentador=True)
    for ws, (rol, wpid) in list(m.conexiones.items()):
        if rol == "participante" and wpid == pid:
            try:
                await ws.send_json(snapshot(m, rol, pid))
            except Exception:  # noqa: BLE001
                m.conexiones.pop(ws, None)
    if len(m.actual) >= len(m.apodos):  # todos respondieron: se cierra sin esperar
        await cerrar_pregunta(m)


# ---------- Mantenimiento ----------

async def cerrar_abandonadas() -> int:
    """Cierra sesiones sin actividad en 2 h (en memoria y en la BD) y descarta las finalizadas hace tiempo."""
    n = 0
    with _registro_lock:
        for pin, m in list(_sesiones.items()):
            if m.estado == "finalizada":
                if m.finalizada_en and time.time() - m.finalizada_en > RETENER_FINALIZADA_S and not m.conexiones:
                    _sesiones.pop(pin, None)
            elif time.time() - m.actividad > EXPIRA_INACTIVA_S:
                await finalizar(m)
                n += 1
    limite = ahora() - timedelta(seconds=EXPIRA_INACTIVA_S)
    with SessionLocal() as db:
        for s in db.scalars(select(SesionVivo).where(SesionVivo.estado != "finalizada", SesionVivo.actividad_en < limite)):
            if s.pin not in _sesiones:
                s.estado = "finalizada"
                s.finalizada_en = ahora()
                n += 1
        db.commit()
    return n


async def bucle_mantenimiento() -> None:
    while True:
        await asyncio.sleep(300)
        try:
            await cerrar_abandonadas()
        except Exception:  # noqa: BLE001
            log.exception("Error al cerrar sesiones abandonadas")
