"""Cálculos estadísticos de la medición de retención y de la comparación entre grupos."""
import math
import statistics
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos import Cuestionario, Intento, Usuario

NOTA_SIGNIFICANCIA = (
    "Para significancia estadística usa la prueba t de Welch en JASP/Excel con el CSV. "
    "El tamaño del efecto (d de Cohen) no sustituye a una prueba de hipótesis."
)


def porcentaje(i: Intento) -> float:
    return 100 * i.puntaje / i.total if i.total else 0.0


def media_y_desviacion(valores: list[float]) -> tuple[int, float | None, float | None]:
    """(n, media, desviación estándar muestral). La desviación es None con menos de 2 datos."""
    n = len(valores)
    if n == 0:
        return 0, None, None
    media = statistics.fmean(valores)
    return n, media, (statistics.stdev(valores) if n > 1 else None)


def d_de_cohen(a: list[float], b: list[float]) -> float | None:
    """d de Cohen con desviación combinada; None si algún grupo tiene menos de 2 datos o no hay variación."""
    if len(a) < 2 or len(b) < 2:
        return None
    var_a, var_b = statistics.variance(a), statistics.variance(b)
    combinada = math.sqrt(((len(a) - 1) * var_a + (len(b) - 1) * var_b) / (len(a) + len(b) - 2))
    if combinada == 0:
        return None
    return (statistics.fmean(a) - statistics.fmean(b)) / combinada


def interpretar_d(d: float | None) -> str:
    if d is None:
        return "No se puede calcular (se necesitan al menos 2 estudiantes por grupo y variación en los datos)."
    magnitud = abs(d)
    if magnitud < 0.2:
        tamano = "trivial"
    elif magnitud < 0.5:
        tamano = "pequeño"
    elif magnitud < 0.8:
        tamano = "mediano"
    else:
        tamano = "grande"
    if tamano == "trivial":
        return "Efecto trivial: los grupos son prácticamente iguales."
    sentido = "A supera a B" if d > 0 else "B supera a A"
    return f"Efecto {tamano} ({sentido})."


@dataclass
class DatosEstudiante:
    usuario: Usuario
    inicial: float | None  # % del intento inicial finalizado
    diferido: float | None  # % del intento diferido finalizado

    @property
    def retencion(self) -> float | None:
        """diferido / inicial x 100; sin definir si falta alguno de los dos o el inicial fue 0 %."""
        if self.inicial is None or self.diferido is None or self.inicial <= 0:
            return None
        return 100 * self.diferido / self.inicial


def datos_por_estudiante(db: Session, c: Cuestionario) -> list[DatosEstudiante]:
    """Intento inicial y diferido (el más antiguo de cada tipo) de cada estudiante; se excluye al creador."""
    filas = db.execute(
        select(Intento, Usuario)
        .join(Usuario, Usuario.id == Intento.usuario_id)
        .where(
            Intento.cuestionario_id == c.id,
            Intento.finalizado.is_(True),
            Intento.tipo.in_(["inicial", "diferido"]),
            Intento.usuario_id != c.creador_id,
        )
        .order_by(Intento.creado_en, Intento.id)
    ).all()
    por_usuario: dict[int, DatosEstudiante] = {}
    for intento, usuario in filas:
        d = por_usuario.setdefault(usuario.id, DatosEstudiante(usuario, None, None))
        if intento.tipo == "inicial" and d.inicial is None:
            d.inicial = porcentaje(intento)
        elif intento.tipo == "diferido" and d.diferido is None:
            d.diferido = porcentaje(intento)
    return list(por_usuario.values())
