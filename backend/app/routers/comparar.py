"""Comparación de dos cuestionarios (grupo de aprendizaje vs. grupo control): diseño cuasi-experimental."""
import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Cuestionario, Usuario
from app.routers.docente import _propio
from app.schemas_api import ComparacionOut, Efecto, GrupoComparacion, MetricaGrupo
from app.seguridad import requiere_docente
from app.services.estadistica import (
    NOTA_SIGNIFICANCIA,
    DatosEstudiante,
    d_de_cohen,
    datos_por_estudiante,
    interpretar_d,
    media_y_desviacion,
)

router = APIRouter(prefix="/api", tags=["comparar"])


def _redondear(v: float | None, cifras: int = 2) -> float | None:
    return None if v is None else round(v, cifras)


def _metrica(valores: list[float]) -> MetricaGrupo:
    n, media, desviacion = media_y_desviacion(valores)
    return MetricaGrupo(n=n, media=_redondear(media), desviacion=_redondear(desviacion))


def _valores(datos: list[DatosEstudiante]) -> dict[str, list[float]]:
    return {
        "inicial": [d.inicial for d in datos if d.inicial is not None],
        "diferido": [d.diferido for d in datos if d.diferido is not None],
        "retencion": [d.retencion for d in datos if d.retencion is not None],
    }


def _efecto(a: list[float], b: list[float]) -> Efecto:
    d = d_de_cohen(a, b)
    diferencia = (sum(a) / len(a) - sum(b) / len(b)) if a and b else None
    return Efecto(diferencia_medias=_redondear(diferencia), d_cohen=_redondear(d), interpretacion=interpretar_d(d))


def _cargar(db: Session, a: int, b: int, docente: Usuario) -> tuple[Cuestionario, Cuestionario]:
    if a == b:
        raise HTTPException(status_code=400, detail="Elige dos cuestionarios distintos para compararlos.")
    return _propio(db, a, docente), _propio(db, b, docente)


@router.get("/comparar", response_model=ComparacionOut)
def comparar(a: int, b: int, docente: Usuario = Depends(requiere_docente), db: Session = Depends(get_db)):
    """Por grupo: n, media y desviación muestral del intento inicial, del diferido y de la retención."""
    ca, cb = _cargar(db, a, b, docente)
    va, vb = _valores(datos_por_estudiante(db, ca)), _valores(datos_por_estudiante(db, cb))

    def grupo(c: Cuestionario, v: dict[str, list[float]]) -> GrupoComparacion:
        return GrupoComparacion(
            id=c.id,
            titulo=c.titulo,
            modo=c.modo or "aprendizaje",
            inicial=_metrica(v["inicial"]),
            diferido=_metrica(v["diferido"]),
            retencion=_metrica(v["retencion"]),
        )

    return ComparacionOut(
        a=grupo(ca, va),
        b=grupo(cb, vb),
        efecto_inicial=_efecto(va["inicial"], vb["inicial"]),
        efecto_diferido=_efecto(va["diferido"], vb["diferido"]),
        efecto_retencion=_efecto(va["retencion"], vb["retencion"]),
        nota=NOTA_SIGNIFICANCIA,
    )


def _num(v: float | None) -> float | str:
    return "" if v is None else round(v, 2)


@router.get("/comparar.csv")
def comparar_csv(a: int, b: int, docente: Usuario = Depends(requiere_docente), db: Session = Depends(get_db)):
    """Datos por estudiante de ambos grupos, anonimizados (E1..En) y solo de quienes consintieron participar."""
    ca, cb = _cargar(db, a, b, docente)
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(["Grupo", "Modo", "Estudiante", "Inicial (%)", "Diferido (%)", "Retención (%)"])
    codigos: dict[int, str] = {}  # un mismo estudiante conserva su código en ambos grupos
    for etiqueta, c in (("A", ca), ("B", cb)):
        for d in datos_por_estudiante(db, c):
            if not d.usuario.consentimiento_investigacion:
                continue
            codigo = codigos.setdefault(d.usuario.id, f"E{len(codigos) + 1}")
            w.writerow([etiqueta, c.modo or "aprendizaje", codigo, _num(d.inicial), _num(d.diferido), _num(d.retencion)])
    contenido = "﻿" + salida.getvalue()  # BOM para que Excel muestre bien las tildes
    return Response(
        content=contenido.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="comparacion_{a}_{b}.csv"'},
    )
