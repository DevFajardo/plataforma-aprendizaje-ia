"""Subtítulos WebVTT y transcripción en texto plano a partir de los segmentos guardados del video."""
from app.schemas import Transcripcion

DURACION_MAXIMA = 8.0  # s: un segmento sin siguiente cercano no se muestra más de este tiempo
DURACION_ULTIMA = 4.0


def _tiempo_vtt(segundos: float) -> str:
    ms = int(round(segundos * 1000))
    h, resto = divmod(ms, 3_600_000)
    m, resto = divmod(resto, 60_000)
    s, ms = divmod(resto, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _limpiar(texto: str) -> str:
    """Quita saltos de línea vacíos y caracteres con significado en WebVTT."""
    # Al escapar «>» el texto nunca contiene la secuencia «-->» que cerraría el cue
    return " ".join(texto.split()).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def a_vtt(transcripcion: Transcripcion) -> str:
    segs = [s for s in transcripcion.segmentos if s.texto.strip()]
    lineas = ["WEBVTT", ""]
    for i, s in enumerate(segs):
        fin = s.inicio + DURACION_ULTIMA
        if i + 1 < len(segs):
            fin = min(segs[i + 1].inicio, s.inicio + DURACION_MAXIMA)
        if fin <= s.inicio:
            fin = s.inicio + 0.5
        lineas += [str(i + 1), f"{_tiempo_vtt(s.inicio)} --> {_tiempo_vtt(fin)}", _limpiar(s.texto), ""]
    return "\n".join(lineas)


def a_texto(transcripcion: Transcripcion) -> str:
    return transcripcion.texto_con_tiempos() + "\n"
