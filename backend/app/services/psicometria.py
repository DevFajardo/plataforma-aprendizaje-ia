"""Análisis de ítems con psicometría clásica (servicio puro, sin acceso a la BD).

Entrada: los ítems (preguntas cerradas con sus opciones y la correcta) y, por cada estudiante, la opción elegida
en cada ítem. Salida: por ítem, índice de dificultad (p), índice de discriminación (D, grupos extremos del 27 %),
correlación punto-biserial (r_pb) y análisis de distractores, con una interpretación en lenguaje docente.

Convenciones:
- El puntaje total de cada estudiante es el número de ítems cerrados que acertó.
- Grupos extremos: se ordena a los estudiantes por puntaje total (de mayor a menor; los empates se mantienen en el orden
  de entrada) y se toma el 27 % superior y el 27 % inferior (k = max(1, redondeo(0,27 · N))).
- D = p(superior) − p(inferior), con p calculado sobre quienes respondieron el ítem en cada grupo.
- r_pb = (M1 − M0) / s · √(p · q), con M1 y M0 las medias del puntaje total de quienes acertaron y fallaron el ítem,
  s la desviación estándar poblacional del puntaje total de quienes respondieron el ítem y q = 1 − p (el puntaje
  total incluye el propio ítem, como en la formulación clásica).
- Un distractor es no funcional si lo elige menos del 5 % de quienes respondieron.
"""
import math
from dataclasses import dataclass, field

MINIMO_RESPUESTAS = 5
UMBRAL_DISTRACTOR = 5.0  # % por debajo del cual un distractor no funciona
FRACCION_EXTREMOS = 0.27


@dataclass
class ItemEntrada:
    id: int
    orden: int
    enunciado: str
    opciones: list[str]
    correcta: str


@dataclass
class Distractor:
    opcion: str
    letra: str
    correcta: bool
    porcentaje: float
    porcentaje_superior: float | None = None
    porcentaje_inferior: float | None = None
    funcional: bool | None = None  # None en la opción correcta
    confunde_mejores: bool = False


@dataclass
class ItemAnalisis:
    pregunta_id: int
    orden: int
    enunciado: str
    n: int
    suficiente: bool
    p: float | None = None
    d: float | None = None
    r_pb: float | None = None
    dificultad: str = ""
    discriminacion: str = ""
    distractores: list[Distractor] = field(default_factory=list)
    observaciones: list[str] = field(default_factory=list)
    revisar: bool = False


def _norm(texto: str) -> str:
    return " ".join(texto.strip().lower().split())


def interpretar_dificultad(p: float) -> str:
    if p >= 0.85:
        return "Muy fácil"
    if p >= 0.70:
        return "Fácil"
    if p >= 0.30:
        return "Dificultad adecuada"
    if p >= 0.15:
        return "Difícil"
    return "Muy difícil"


def interpretar_discriminacion(d: float) -> str:
    if d >= 0.40:
        return "Discrimina muy bien"
    if d >= 0.30:
        return "Discrimina bien"
    if d >= 0.20:
        return "Discrimina de forma aceptable"
    if d >= 0.0:
        return "Discrimina poco"
    return "Discriminación negativa"


def _media(valores: list[float]) -> float:
    return sum(valores) / len(valores)


def correlacion_punto_biserial(totales: list[float], aciertos: list[bool]) -> float | None:
    """r_pb entre un ítem (acierto/fallo) y el puntaje total; None si no se puede calcular."""
    n = len(totales)
    n1 = sum(aciertos)
    if n < 2 or n1 == 0 or n1 == n:
        return None
    media = _media(totales)
    s = math.sqrt(sum((t - media) ** 2 for t in totales) / n)
    if s == 0:
        return None
    m1 = _media([t for t, a in zip(totales, aciertos) if a])
    m0 = _media([t for t, a in zip(totales, aciertos) if not a])
    p = n1 / n
    return (m1 - m0) / s * math.sqrt(p * (1 - p))


def analizar_items(
    items: list[ItemEntrada], respuestas: list[dict[int, str]], minimo: int = MINIMO_RESPUESTAS
) -> list[ItemAnalisis]:
    """`respuestas[i][pregunta_id]` es el texto elegido por el estudiante `i` (ausente = no respondió)."""
    # Opción elegida normalizada -> índice de opción (None si no coincide con ninguna)
    correctas = {it.id: _norm(it.correcta) for it in items}
    totales = [sum(1 for it in items if _norm(r.get(it.id, "")) == correctas[it.id] and it.id in r) for r in respuestas]

    orden_desc = sorted(range(len(respuestas)), key=lambda i: -totales[i])  # estable: respeta el orden de entrada
    k = max(1, round(FRACCION_EXTREMOS * len(respuestas))) if respuestas else 0
    superior = set(orden_desc[:k])
    inferior = set(orden_desc[len(orden_desc) - k:]) if k else set()

    salida: list[ItemAnalisis] = []
    for it in items:
        quienes = [i for i, r in enumerate(respuestas) if it.id in r]
        n = len(quienes)
        res = ItemAnalisis(pregunta_id=it.id, orden=it.orden, enunciado=it.enunciado, n=n, suficiente=n >= minimo)
        if not res.suficiente:
            salida.append(res)
            continue

        acierta = [_norm(respuestas[i][it.id]) == correctas[it.id] for i in quienes]
        res.p = round(sum(acierta) / n, 4)
        res.dificultad = interpretar_dificultad(res.p)

        sup = [i for i in quienes if i in superior]
        inf = [i for i in quienes if i in inferior]
        if sup and inf:
            p_sup = sum(_norm(respuestas[i][it.id]) == correctas[it.id] for i in sup) / len(sup)
            p_inf = sum(_norm(respuestas[i][it.id]) == correctas[it.id] for i in inf) / len(inf)
            res.d = round(p_sup - p_inf, 4)
            res.discriminacion = interpretar_discriminacion(res.d)

        r = correlacion_punto_biserial([totales[i] for i in quienes], acierta)
        res.r_pb = None if r is None else round(r, 4)

        # Distractores: % que elige cada opción (de quienes respondieron)
        for idx, opcion in enumerate(it.opciones):
            elegida = [i for i in quienes if _norm(respuestas[i][it.id]) == _norm(opcion)]
            es_correcta = _norm(opcion) == correctas[it.id]
            pct = 100 * len(elegida) / n
            dis = Distractor(
                opcion=opcion,
                letra=chr(65 + idx),
                correcta=es_correcta,
                porcentaje=round(pct, 1),
                porcentaje_superior=round(100 * sum(1 for i in sup if i in elegida) / len(sup), 1) if sup else None,
                porcentaje_inferior=round(100 * sum(1 for i in inf if i in elegida) / len(inf), 1) if inf else None,
            )
            if not es_correcta:
                dis.funcional = pct >= UMBRAL_DISTRACTOR
                if (
                    dis.porcentaje_superior is not None
                    and dis.porcentaje_inferior is not None
                    and dis.porcentaje_superior > dis.porcentaje_inferior
                ):
                    dis.confunde_mejores = True
            res.distractores.append(dis)

        _observaciones(res)
        salida.append(res)
    return salida


def _observaciones(res: ItemAnalisis) -> None:
    """Redacta la interpretación en lenguaje docente y marca si el ítem conviene revisarlo."""
    obs = res.observaciones
    if res.p is not None and res.p >= 0.85:
        obs.append("Muy fácil: casi todos acertaron; sirve como calentamiento, pero aporta poca información.")
    elif res.p is not None and res.p < 0.15:
        obs.append("Muy difícil: casi nadie acertó; revisa si la pregunta es clara o si el tema se explicó en el video.")
        res.revisar = True
    if res.d is not None:
        if res.d < 0:
            obs.append("Revisar: los estudiantes con menor puntaje acertaron más que los de mayor puntaje.")
            res.revisar = True
        elif res.d < 0.20:
            obs.append("Discrimina poco entre quienes dominan el tema y quienes no.")
        elif res.d >= 0.30:
            obs.append("Discrimina bien entre estudiantes con alto y bajo desempeño.")
    for dis in res.distractores:
        if dis.confunde_mejores:
            obs.append(f"Revisar: la opción {dis.letra} confunde a los mejores estudiantes (la eligen más que a los de menor puntaje).")
            res.revisar = True
    no_func = [d.letra for d in res.distractores if d.funcional is False]
    if no_func:
        obs.append(f"Distractor(es) no funcional(es): opción {', '.join(no_func)} (menos del {UMBRAL_DISTRACTOR:.0f} % la elige); conviene reemplazarlos.")
    if not obs:
        obs.append("Sin observaciones: el ítem funciona dentro de lo esperado.")
