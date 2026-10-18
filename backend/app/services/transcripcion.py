"""Obtención de la transcripción de un video de YouTube.

Estrategia en dos pasos:
  1. Subtítulos existentes (rápido y gratuito) con youtube-transcript-api.
  2. Respaldo: descargar solo el audio con yt-dlp y transcribirlo con Groq Whisper.
"""
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.config import settings
from app.schemas import Segmento, Transcripcion

log = logging.getLogger(__name__)

LIMITE_BYTES = 25 * 1024 * 1024  # límite de Groq para archivos de audio
DURACION_TROZO = 600  # segundos (~10 min)


def _id_vimeo(url: str) -> str | None:
    """ID numérico de una URL de Vimeo (vimeo.com/123, /channels/x/123, player.vimeo.com/video/123, /123/hash)."""
    try:
        p = urlparse(url.strip())
    except Exception:  # pragma: no cover
        return None
    host = (p.hostname or "").lower().removeprefix("www.")
    if host not in ("vimeo.com", "player.vimeo.com"):
        return None
    partes = [x for x in p.path.split("/") if x]
    if host == "player.vimeo.com":
        partes = partes[1:] if partes[:1] == ["video"] else []
    for parte in partes:
        if parte.isdigit() and len(parte) <= 12:
            return parte
    return None


def hash_vimeo(url: str) -> str | None:
    """Hash de un video no listado de Vimeo (vimeo.com/123/hash o ?h=hash); None si no tiene."""
    p = urlparse(url.strip())
    h = (parse_qs(p.query).get("h") or [None])[0]
    if h and h.isalnum():
        return h
    partes = [x for x in p.path.split("/") if x]
    for i, parte in enumerate(partes[:-1]):
        if parte.isdigit() and partes[i + 1].isalnum() and not partes[i + 1].isdigit() and 6 <= len(partes[i + 1]) <= 20:
            return partes[i + 1]
    return None


def identificar_video(url: str) -> tuple[str, str]:
    """Devuelve (plataforma, id) con plataforma "youtube" o "vimeo"; ValueError si la URL no es válida."""
    try:
        return "youtube", extraer_video_id(url)
    except ValueError:
        pass
    video_id = _id_vimeo(url)
    if video_id:
        return "vimeo", video_id
    raise ValueError("La URL no corresponde a un video de YouTube o Vimeo válido.")


def extraer_video_id(url: str) -> str:
    """Extrae el ID de 11 caracteres de una URL de YouTube; ValueError si no es válida."""
    try:
        p = urlparse(url.strip())
    except Exception as e:  # pragma: no cover
        raise ValueError("URL inválida") from e
    host = (p.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    video_id = None
    if host == "youtu.be":
        video_id = p.path.strip("/").split("/")[0]
    elif host in ("youtube.com", "music.youtube.com", "youtube-nocookie.com"):
        partes = [x for x in p.path.split("/") if x]
        if p.path.startswith("/watch"):
            video_id = (parse_qs(p.query).get("v") or [None])[0]
        elif len(partes) >= 2 and partes[0] in ("shorts", "embed", "live", "v"):
            video_id = partes[1]
    if not video_id or len(video_id) != 11 or not all(c.isalnum() or c in "-_" for c in video_id):
        raise ValueError("La URL no corresponde a un video de YouTube válido.")
    return video_id


def _ruta_cookies() -> str | None:
    """Archivo cookies.txt (formato Netscape) exportado del navegador, si está configurado y existe.

    Con las cookies de una sesión de YouTube, las peticiones parecen de un usuario normal y
    YouTube deja de responder "Sign in to confirm you're not a bot" / 429.
    """
    if not settings.youtube_cookies:
        return None
    ruta = Path(settings.youtube_cookies)
    if not ruta.is_absolute():
        ruta = Path(__file__).resolve().parents[2] / ruta
    if not ruta.is_file():
        log.warning("YOUTUBE_COOKIES apunta a un archivo que no existe: %s", ruta)
        return None
    return str(ruta)


def _desde_subtitulos(video_id: str) -> Transcripcion:
    from youtube_transcript_api import YouTubeTranscriptApi

    http_client = None
    cookies = _ruta_cookies()
    if cookies:
        import requests
        from http.cookiejar import MozillaCookieJar

        jar = MozillaCookieJar(cookies)
        jar.load(ignore_discard=True, ignore_expires=True)
        http_client = requests.Session()
        http_client.cookies = jar  # type: ignore[assignment]

    fetched = YouTubeTranscriptApi(http_client=http_client).fetch(video_id, languages=["es", "es-419", "en"])
    segmentos = [Segmento(inicio=s.start, texto=s.text.replace("\n", " ").strip()) for s in fetched]
    if not segmentos:
        raise RuntimeError("Los subtítulos están vacíos")
    return Transcripcion(
        fuente="subtitulos_youtube",
        idioma=getattr(fetched, "language_code", "") or "",
        segmentos=segmentos,
    )


def _ruta_ffmpeg() -> str:
    """Devuelve el ejecutable de ffmpeg (FFMPEG_PATH puede ser carpeta o exe)."""
    if settings.ffmpeg_path:
        p = Path(settings.ffmpeg_path)
        return str(p / "ffmpeg.exe") if p.is_dir() else str(p)
    return shutil.which("ffmpeg") or "ffmpeg"


ESTADOS_EN_VIVO = ("is_live", "is_upcoming", "post_live")


def verificar_video_procesable(info: dict | None) -> None:
    """RuntimeError (mensaje para el usuario) si el video es una transmisión en vivo o supera MAX_DURACION_MIN."""
    info = info or {}
    if info.get("is_live") or info.get("live_status") in ESTADOS_EN_VIVO:
        raise RuntimeError("No se procesan transmisiones en vivo ni estrenos programados; usa un video ya publicado.")
    duracion = info.get("duration")
    maximo = settings.max_duracion_min
    if isinstance(duracion, (int, float)) and duracion > maximo * 60:
        raise RuntimeError(
            f"El video dura {round(duracion / 60)} min y el máximo permitido es {maximo} min. "
            "Usa un video más corto."
        )


def _descargar_audio(url: str, carpeta: Path) -> Path:
    import yt_dlp

    ruta_node = shutil.which("node")
    opciones = {
        "format": "bestaudio/best",
        "outtmpl": str(carpeta / "audio.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        # yt-dlp necesita un runtime de JavaScript (Node.js) para resolver los desafíos de YouTube
        "js_runtimes": {"node": {"path": ruta_node} if ruta_node else {}},
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "32"}
        ],
        "postprocessor_args": {"extractaudio": ["-ac", "1", "-ar", "16000", "-b:a", "32k"]},
    }
    if settings.ffmpeg_path:
        opciones["ffmpeg_location"] = settings.ffmpeg_path
    cookies = _ruta_cookies()
    if cookies and "youtube" in url:  # las cookies de YouTube no se envían a otras plataformas
        opciones["cookiefile"] = cookies
    with yt_dlp.YoutubeDL(opciones) as ydl:
        # Primero solo los metadatos: se rechazan transmisiones en vivo y videos demasiado largos
        info = ydl.extract_info(url, download=False)
        verificar_video_procesable(info)
        ydl.process_ie_result(info, download=True)
    archivo = carpeta / "audio.mp3"
    if not archivo.exists():
        raise RuntimeError("No se pudo descargar el audio del video")
    return archivo


def _dividir_audio(archivo: Path, carpeta: Path) -> list[Path]:
    patron = carpeta / "trozo_%03d.mp3"
    subprocess.run(
        [_ruta_ffmpeg(), "-y", "-i", str(archivo), "-f", "segment",
         "-segment_time", str(DURACION_TROZO), "-c", "copy", str(patron)],
        check=True, capture_output=True,
    )
    return sorted(carpeta.glob("trozo_*.mp3"))


def _whisper(archivo: Path, desplazamiento: float) -> list[Segmento]:
    from groq import Groq

    cliente = Groq(api_key=settings.groq_api_key)
    parametros: dict = {}
    if settings.idioma_transcripcion.strip():  # vacío = detección automática de Whisper
        parametros["language"] = settings.idioma_transcripcion.strip()
    resp = cliente.audio.transcriptions.create(
        file=(archivo.name, archivo.read_bytes()),
        model=settings.groq_whisper_model,
        response_format="verbose_json",
        **parametros,
    )
    segs = getattr(resp, "segments", None) or []
    salida = []
    for s in segs:
        if isinstance(s, dict):
            texto, inicio = s.get("text"), s.get("start")
        else:
            texto, inicio = getattr(s, "text", ""), getattr(s, "start", 0)
        texto = (texto or "").strip()
        if texto:
            salida.append(Segmento(inicio=float(inicio or 0) + desplazamiento, texto=texto))
    return salida


def transcribir_archivo(ruta: Path) -> Transcripcion:
    """Transcribe un archivo de audio (mp3) con Groq Whisper, dividiéndolo si supera el límite de 25 MB."""
    if not settings.groq_api_key:
        raise RuntimeError("No hay GROQ_API_KEY configurada para transcribir el audio.")
    if ruta.stat().st_size > LIMITE_BYTES:
        trozos = _dividir_audio(ruta, ruta.parent)
    else:
        trozos = [ruta]
    segmentos: list[Segmento] = []
    for i, t in enumerate(trozos):
        segmentos += _whisper(t, i * DURACION_TROZO if len(trozos) > 1 else 0)
    if not segmentos:
        raise RuntimeError("Whisper no devolvió texto. ¿El archivo tiene voz?")
    return Transcripcion(fuente="whisper_groq", idioma=settings.idioma_transcripcion.strip() or "auto", segmentos=segmentos)


def extraer_audio(entrada: Path, carpeta: Path) -> Path:
    """Extrae el audio de un video/audio con ffmpeg: mono, 16 kHz, mp3 a ~32 kbps."""
    salida = carpeta / "audio.mp3"
    r = subprocess.run(
        [_ruta_ffmpeg(), "-y", "-i", str(entrada), "-vn", "-ac", "1", "-ar", "16000",
         "-b:a", "32k", str(salida)],
        capture_output=True,
    )
    if r.returncode != 0 or not salida.exists():
        log.error("ffmpeg falló: %s", r.stderr.decode("utf-8", "ignore")[-500:])
        raise RuntimeError("No se pudo extraer el audio del archivo. ¿Es un video o audio válido?")
    return salida


def transcribir_subida(ruta: Path) -> Transcripcion:
    """Archivo subido por el usuario (video o audio) -> audio mp3 -> Whisper."""
    carpeta = Path(tempfile.mkdtemp(prefix="plataforma_subida_"))
    try:
        return transcribir_archivo(extraer_audio(ruta, carpeta))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def _desde_whisper(url: str) -> Transcripcion:
    if not settings.groq_api_key:
        raise RuntimeError(
            "El video no tiene subtítulos y no hay GROQ_API_KEY configurada para transcribir el audio."
        )
    carpeta = Path(tempfile.mkdtemp(prefix="plataforma_audio_"))
    try:
        return transcribir_archivo(_descargar_audio(url, carpeta))
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


def obtener_transcripcion(url: str) -> Transcripcion:
    """YouTube: subtítulos y, si fallan, audio + Whisper (Groq). Vimeo: siempre audio + Whisper."""
    plataforma, video_id = identificar_video(url)
    if plataforma == "vimeo":
        # El reproductor incrustado no exige iniciar sesión (vimeo.com/ID sí lo pide en videos públicos)
        h = hash_vimeo(url)
        return _desde_whisper(f"https://player.vimeo.com/video/{video_id}" + (f"?h={h}" if h else ""))
    try:
        return _desde_subtitulos(video_id)
    except Exception as e:
        log.warning("Sin subtítulos para %s (%s); usando Whisper", video_id, type(e).__name__)
    return _desde_whisper(f"https://www.youtube.com/watch?v={video_id}")
