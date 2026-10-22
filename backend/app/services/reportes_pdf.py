"""Reportes PDF institucionales con reportlab (fuente Helvetica, sin incrustar tipografías)."""
import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as lienzo
from reportlab.platypus import BaseDocTemplate, Flowable, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle

from app.modelos import ahora
from app.schemas_academico import CoordinacionOut
from app.schemas_api import ResultadosOut

AZUL = colors.HexColor("#0B468A")
NARANJA = colors.HexColor("#E88A37")
GRIS = colors.HexColor("#5B6573")
BORDE = colors.HexColor("#D5DAE1")
PISTA = colors.HexColor("#E6EAF0")
FONDO_CABECERA = colors.HexColor("#EAF1FA")
COLOR_SEMAFORO = {
    "verde": colors.HexColor("#2E8B57"),
    "amarillo": colors.HexColor("#D9A21B"),
    "rojo": colors.HexColor("#C0392B"),
    "sin_datos": colors.HexColor("#9AA3AE"),
}
TEXTO_SEMAFORO = {"verde": "Logrado", "amarillo": "En desarrollo", "rojo": "Crítico", "sin_datos": "Sin datos"}
PIE = "Plataforma de Aprendizaje Activo — Proyecto académico CUL"
ALTO_CABECERA = 30 * mm


def _semaforo(valor: float | None) -> str:
    if valor is None:
        return "sin_datos"
    return "verde" if valor >= 70 else "amarillo" if valor >= 50 else "rojo"


def _fecha_local(dt: datetime | None = None) -> str:
    return (dt or ahora()).astimezone().strftime("%d/%m/%Y %H:%M")


class LienzoNumerado(lienzo.Canvas):
    """Lienzo que dibuja el pie con «Página n de m» (necesita conocer el total, por eso guarda las páginas)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas: list[dict] = []

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            self._pie(total)
            super().showPage()
        super().save()

    def _pie(self, total: int):
        ancho, _ = A4
        self.setStrokeColor(BORDE)
        self.setLineWidth(0.6)
        self.line(18 * mm, 16 * mm, ancho - 18 * mm, 16 * mm)
        self.setFont("Helvetica", 8)
        self.setFillColor(GRIS)
        self.drawString(18 * mm, 11 * mm, PIE)
        self.drawRightString(ancho - 18 * mm, 11 * mm, f"Página {self._pageNumber} de {total}")


class Barra(Flowable):
    """Barra de logro (0 a 100) coloreada por semáforo, para usar dentro de tablas."""

    def __init__(self, valor: float | None, ancho: float = 38 * mm, alto: float = 3.6 * mm):
        super().__init__()
        self.valor, self.width, self.height = valor, ancho, alto

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(PISTA)
        c.roundRect(0, 0, self.width, self.height, 1.5, stroke=0, fill=1)
        if self.valor is not None:
            c.setFillColor(COLOR_SEMAFORO[_semaforo(self.valor)])
            c.roundRect(0, 0, max(self.width * min(self.valor, 100) / 100, 1.5), self.height, 1.5, stroke=0, fill=1)


def _estilos():
    base = getSampleStyleSheet()
    return {
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12, textColor=AZUL, spaceBefore=10, spaceAfter=5),
        "p": ParagraphStyle("p", parent=base["BodyText"], fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#1F2933")),
        "nota": ParagraphStyle("nota", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=8, leading=10, textColor=GRIS),
        "celda": ParagraphStyle("celda", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=10),
        "celda_b": ParagraphStyle("celda_b", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=AZUL),
    }


def _construir(titulo: str, subtitulo: str, historia: list) -> bytes:
    """Arma el documento A4 con franja azul, línea naranja, título, subtítulo y fecha de generación."""
    salida = io.BytesIO()
    ancho, alto = A4
    generado = f"Generado el {_fecha_local()}"

    def cabecera(c, _doc):
        c.saveState()
        c.setFillColor(AZUL)
        c.rect(0, alto - ALTO_CABECERA, ancho, ALTO_CABECERA, stroke=0, fill=1)
        c.setFillColor(NARANJA)
        c.rect(0, alto - ALTO_CABECERA - 1.4 * mm, ancho, 1.4 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 8)
        c.drawString(18 * mm, alto - 9 * mm, "CORPORACIÓN UNIVERSITARIA LATINOAMERICANA — CUL")
        c.setFont("Helvetica-Bold", 16)
        c.drawString(18 * mm, alto - 17.5 * mm, titulo[:70])
        c.setFont("Helvetica", 9)
        c.drawString(18 * mm, alto - 24 * mm, subtitulo[:110])
        c.drawRightString(ancho - 18 * mm, alto - 9 * mm, generado)
        c.restoreState()

    doc = BaseDocTemplate(
        salida, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=ALTO_CABECERA + 8 * mm, bottomMargin=22 * mm,
        title=titulo, author="Plataforma de Aprendizaje Activo — CUL", subject=subtitulo,
    )
    marco = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="contenido", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="institucional", frames=[marco], onPage=cabecera)])
    doc.build(historia, canvasmaker=LienzoNumerado)
    return salida.getvalue()


def _tabla(filas: list[list], anchos: list[float], alineadas_derecha: tuple[int, ...] = ()) -> Table:
    t = Table(filas, colWidths=anchos, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FC")]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for col in alineadas_derecha:
        estilo.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(estilo))
    return t


def _p(texto: str, estilo) -> Paragraph:
    return Paragraph(escape(str(texto)), estilo)


def _pct(v: float | None) -> str:
    return "—" if v is None else f"{v:.1f} %".replace(".", ",")


def _resumen_metricas(items: list[tuple[str, str]]) -> Table:
    est = _estilos()
    celdas = [[Paragraph(f'<font size="14" color="#0B468A"><b>{escape(v)}</b></font><br/><font size="7.5" color="#5B6573">{escape(k)}</font>', est["p"]) for k, v in items]]
    t = Table(celdas, colWidths=[174 * mm / len(items)] * len(items))
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, BORDE), ("INNERGRID", (0, 0), (-1, -1), 0.6, BORDE),
        ("BACKGROUND", (0, 0), (-1, -1), FONDO_CABECERA), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ---------- (a) Reporte de resultados de aprendizaje del programa ----------

def reporte_ra_pdf(d: CoordinacionOut) -> bytes:
    est = _estilos()
    periodo = d.periodo or "Todos los periodos"
    h: list = [
        _resumen_metricas([
            ("Logro global", _pct(d.logro_global)), ("Respuestas evaluadas", str(d.respuestas)), ("Estudiantes evaluados", str(d.estudiantes)),
        ]),
        Spacer(1, 4),
        _p("Logro = respuestas correctas / respuestas a preguntas cerradas de estudiantes matriculados. "
           "Semáforo: verde >= 70 %, amarillo 50 a 69 %, rojo < 50 %.", est["nota"]),
        Paragraph("Logro por resultado de aprendizaje", est["h2"]),
    ]
    if d.ras:
        filas = [["RA", "Descripción", "Logro", "", "Resp.", "Estud.", "Estado"]]
        for r in d.ras:
            filas.append([_p(r.codigo, est["celda_b"]), _p(r.descripcion, est["celda"]), _pct(r.logro), Barra(r.logro, 24 * mm), str(r.respuestas), str(r.estudiantes), TEXTO_SEMAFORO[r.semaforo]])
        h.append(_tabla(filas, [13 * mm, 62 * mm, 17 * mm, 27 * mm, 12 * mm, 13 * mm, 24 * mm], (2, 4, 5)))
    else:
        h.append(_p("No hay resultados de aprendizaje definidos para este programa.", est["p"]))

    h.append(Paragraph("Distribución por nivel de la taxonomía de Bloom", est["h2"]))
    filas = [["Nivel", "Preguntas", "Respuestas", "Logro", ""]]
    for b in d.bloom:
        filas.append([b.nivel.capitalize(), str(b.preguntas), str(b.respuestas), _pct(b.logro), Barra(b.logro, 40 * mm)])
    h.append(_tabla(filas, [34 * mm, 24 * mm, 26 * mm, 24 * mm, 48 * mm], (1, 2, 3)))

    h.append(Paragraph("Desempeño por asignatura y grupo", est["h2"]))
    if d.asignaturas:
        filas = [["Asignatura / grupo", "Docente", "Logro", "", "Resp.", "Estud."]]
        for a in d.asignaturas:
            filas.append([_p(f"{a.codigo} · {a.nombre}", est["celda_b"]), "", _pct(a.logro), Barra(a.logro, 24 * mm), str(a.respuestas), str(a.estudiantes)])
            for g in a.grupos:
                filas.append([_p(f"    {g.nombre} ({g.periodo})", est["celda"]), _p(g.docente, est["celda"]), _pct(g.logro), Barra(g.logro, 24 * mm), str(g.respuestas), str(g.estudiantes)])
        h.append(_tabla(filas, [62 * mm, 40 * mm, 17 * mm, 27 * mm, 14 * mm, 14 * mm], (2, 4, 5)))
    else:
        h.append(_p("Aún no hay asignaturas con grupos en este programa.", est["p"]))

    h.append(Paragraph("Tendencia semanal del logro", est["h2"]))
    if d.tendencia:
        filas = [["Semana (inicia el lunes)", "Logro", "", "Respuestas"]]
        for t in d.tendencia[-26:]:
            filas.append([t.semana, _pct(t.logro), Barra(t.logro, 60 * mm), str(t.respuestas)])
        h.append(_tabla(filas, [44 * mm, 24 * mm, 66 * mm, 26 * mm], (1, 3)))
    else:
        h.append(_p("Sin intentos finalizados en el periodo seleccionado.", est["p"]))
    return _construir("Reporte de resultados de aprendizaje", f"Programa: {d.programa_nombre} · Periodo: {periodo}", h)


# ---------- (b) Reporte de resultados de un cuestionario / grupo ----------

def reporte_cuestionario_pdf(r: ResultadosOut, programa: str, asignatura: str, grupo: str, periodo: str) -> bytes:
    est = _estilos()
    h: list = [
        _p(f"Cuestionario: {r.titulo}", est["p"]),
        _p(f"Asignatura: {asignatura} · Grupo: {grupo}", est["p"]),
        Spacer(1, 6),
        _resumen_metricas([
            ("Intentos finalizados", str(r.total_intentos)), ("Estudiantes", str(r.estudiantes_unicos)), ("Promedio", _pct(r.promedio_porcentaje)),
        ]),
        Paragraph("Acierto por pregunta", est["h2"]),
    ]
    filas = [["#", "Pregunta", "RA", "Bloom", "Acierto", ""]]
    for p in r.preguntas:
        acierto = p.porcentaje_acierto
        filas.append([
            str(p.orden + 1), _p(p.enunciado[:160], est["celda"]), p.ra_codigo or "—", (p.nivel_bloom or "—").capitalize(),
            "Abierta" if p.tipo == "abierta" else _pct(acierto), "" if p.tipo == "abierta" else Barra(acierto, 22 * mm),
        ])
    h.append(_tabla(filas, [8 * mm, 74 * mm, 12 * mm, 22 * mm, 17 * mm, 25 * mm], (4,)))

    h.append(Paragraph("Análisis de ítems (psicometría clásica)", est["h2"]))
    h.append(_p(f"Calculado con {r.items_intentos} intento(s) inicial(es) finalizado(s). p = índice de dificultad; D = discriminación "
                f"(27 % superior vs. inferior); r_pb = correlación punto-biserial. Se muestran índices con al menos {r.items_minimo} respuestas.", est["nota"]))
    if r.items:
        f_items = [["#", "Pregunta", "n", "p", "D", "r_pb", "Interpretación"]]
        for it in r.items:
            if not it.suficiente:
                f_items.append([str(it.orden + 1), _p(it.enunciado[:110], est["celda"]), str(it.n), "—", "—", "—", _p("Datos insuficientes", est["celda"])])
                continue
            interpretacion = " · ".join(x for x in (it.dificultad, it.discriminacion) if x)
            if it.revisar:
                interpretacion = "REVISAR: " + interpretacion
            for dis in it.distractores:
                if dis.confunde_mejores:
                    interpretacion += f". Opción {dis.letra} confunde a los mejores"
            no_func = [d.letra for d in it.distractores if d.funcional is False]
            if no_func:
                interpretacion += f". Distractor no funcional: {', '.join(no_func)}"
            f_items.append([
                str(it.orden + 1), _p(it.enunciado[:110], est["celda"]), str(it.n),
                "—" if it.p is None else f"{it.p:.2f}".replace(".", ","),
                "—" if it.d is None else f"{it.d:.2f}".replace(".", ","),
                "—" if it.r_pb is None else f"{it.r_pb:.2f}".replace(".", ","),
                _p(interpretacion, est["celda"]),
            ])
        h.append(_tabla(f_items, [7 * mm, 54 * mm, 8 * mm, 11 * mm, 11 * mm, 12 * mm, 71 * mm], (2, 3, 4, 5)))
    else:
        h.append(_p("El cuestionario no tiene preguntas cerradas para analizar.", est["p"]))

    g, ret = r.ganancia, r.retencion
    h.append(Paragraph("Ganancia de aprendizaje y retención", est["h2"]))
    if g.estudiantes:
        h.append(_p(f"Ganancia: {g.estudiantes} estudiantes con 2 o más intentos; promedio del primer intento {_pct(g.promedio_primer_intento)}, "
                    f"del último {_pct(g.promedio_ultimo_intento)} (diferencia {_pct(g.diferencia_puntos)} puntos).", est["p"]))
    else:
        h.append(_p("Ganancia: aún no hay estudiantes con 2 o más intentos.", est["p"]))
    if ret.estudiantes:
        h.append(_p(f"Retención: {ret.estudiantes} estudiantes con intento inicial y diferido; promedio inicial {_pct(ret.promedio_inicial)}, "
                    f"diferido {_pct(ret.promedio_diferido)}.", est["p"]))
    else:
        h.append(_p("Retención: sin intentos diferidos todavía.", est["p"]))

    h.append(Paragraph("Intentos finalizados", est["h2"]))
    if r.intentos:
        filas = [["Estudiante", "Tipo", "Puntaje", "Porcentaje", "Fecha"]]
        for i in r.intentos[:300]:
            filas.append([_p(i.nombre, est["celda"]), i.tipo.capitalize(), f"{i.puntaje}/{i.total}", _pct(i.porcentaje), _fecha_local(i.fecha)])
        h.append(_tabla(filas, [62 * mm, 26 * mm, 22 * mm, 26 * mm, 38 * mm], (2, 3)))
        if len(r.intentos) > 300:
            h.append(_p(f"Se muestran 300 de {len(r.intentos)} intentos.", est["nota"]))
    else:
        h.append(_p("Todavía no hay intentos finalizados.", est["p"]))
    return _construir("Resultados del cuestionario", f"Programa: {programa} · Periodo: {periodo}", h)
