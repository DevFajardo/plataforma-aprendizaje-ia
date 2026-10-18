"""Cálculo e interpretación de la escala de usabilidad SUS (System Usability Scale)."""

ITEMS_SUS = [
    "Creo que me gustaría usar este sistema con frecuencia.",
    "Encontré el sistema innecesariamente complejo.",
    "Pensé que el sistema era fácil de usar.",
    "Creo que necesitaría el apoyo de un técnico para poder usar este sistema.",
    "Encontré que las diversas funciones de este sistema estaban bien integradas.",
    "Pensé que había demasiada inconsistencia en este sistema.",
    "Imagino que la mayoría de las personas aprenderían a usar este sistema muy rápidamente.",
    "Encontré el sistema muy engorroso de usar.",
    "Me sentí muy seguro/a usando el sistema.",
    "Necesité aprender muchas cosas antes de poder empezar a usar este sistema.",
]

CATEGORIAS = ["Pobre", "Aceptable bajo", "Bueno", "Excelente"]


def calcular_puntaje(respuestas: list[int]) -> float:
    """Puntaje SUS 0-100.

    Ítems impares (1, 3, 5, 7, 9) aportan (r - 1); pares (2, 4, 6, 8, 10) aportan (5 - r).
    La suma (0-40) se multiplica por 2,5.
    """
    if len(respuestas) != 10 or any(not 1 <= r <= 5 for r in respuestas):
        raise ValueError("SUS requiere exactamente 10 respuestas entre 1 y 5.")
    total = 0
    for numero, r in enumerate(respuestas, start=1):
        total += (r - 1) if numero % 2 == 1 else (5 - r)
    return total * 2.5


def interpretar(puntaje: float) -> str:
    """<51 Pobre; 51-68 Aceptable bajo; 68-80,3 Bueno; >80,3 Excelente."""
    if puntaje < 51:
        return "Pobre"
    if puntaje < 68:
        return "Aceptable bajo"
    if puntaje <= 80.3:
        return "Bueno"
    return "Excelente"
