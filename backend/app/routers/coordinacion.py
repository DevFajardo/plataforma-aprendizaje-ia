"""Panel de coordinación (logro por RA), alertas tempranas y reportes PDF institucionales."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import AlertaSeguimiento, Cuestionario, Grupo, Usuario
from app.routers.cursos import grupos_visibles
from app.routers.docente import _calcular_resultados, _propio
from app.schemas_academico import AlertaOut, AtenderAlertaIn, CoordinacionOut, SeguimientoOut
from app.seguridad import requiere_coordinacion, requiere_docente, requiere_seguimiento
from app.services.alertas import calcular_alertas
from app.services.logro import calcular_coordinacion
from app.services.reportes_pdf import reporte_cuestionario_pdf, reporte_ra_pdf

router = APIRouter(prefix="/api", tags=["coordinacion"])


@router.get("/coordinacion/resumen", response_model=CoordinacionOut)
def resumen(
    programa_id: int | None = None,
    periodo: str | None = None,
    usuario: Usuario = Depends(requiere_coordinacion),
    db: Session = Depends(get_db),
):
    return calcular_coordinacion(db, usuario, programa_id, periodo)


def _pdf(contenido: bytes, nombre: str) -> Response:
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get("/coordinacion/reporte-ra.pdf")
def reporte_ra(
    programa_id: int | None = None,
    periodo: str | None = None,
    usuario: Usuario = Depends(requiere_coordinacion),
    db: Session = Depends(get_db),
):
    d = calcular_coordinacion(db, usuario, programa_id, periodo)
    return _pdf(reporte_ra_pdf(d), f"reporte_ra_{periodo or 'todos'}.pdf")


@router.get("/cuestionarios/{cuestionario_id}/reporte.pdf")
def reporte_cuestionario(cuestionario_id: int, docente: Usuario = Depends(requiere_docente), db: Session = Depends(get_db)):
    c: Cuestionario = _propio(db, cuestionario_id, docente)
    r = _calcular_resultados(db, c)
    if c.grupo:
        grupo, asignatura, programa, periodo = c.grupo.nombre, c.grupo.asignatura.nombre, c.grupo.asignatura.programa.nombre, c.grupo.periodo
    else:
        grupo = asignatura = programa = periodo = "Sin grupo asignado"
    return _pdf(reporte_cuestionario_pdf(r, programa, asignatura, grupo, periodo), f"resultados_{cuestionario_id}.pdf")


# ---------- Alertas tempranas ----------

@router.get("/alertas", response_model=list[AlertaOut])
def alertas(
    grupo_id: int | None = None,
    usuario: Usuario = Depends(requiere_seguimiento),
    db: Session = Depends(get_db),
):
    """Alertas activas de los grupos del docente / del programa del coordinador / de todos (admin)."""
    grupos = grupos_visibles(db, usuario)
    if grupo_id is not None:
        grupos = [g for g in grupos if g.id == grupo_id]
    return calcular_alertas(db, grupos)


@router.post("/alertas/atender", response_model=SeguimientoOut, status_code=201)
def atender(datos: AtenderAlertaIn, usuario: Usuario = Depends(requiere_seguimiento), db: Session = Depends(get_db)):
    """Marca como atendida la alerta vigente del estudiante en el grupo (con una nota opcional)."""
    grupo = db.get(Grupo, datos.grupo_id)
    if grupo is None or grupo not in grupos_visibles(db, usuario):
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    vigente = next((a for a in calcular_alertas(db, [grupo]) if a.estudiante_id == datos.estudiante_id), None)
    if vigente is None:
        raise HTTPException(status_code=404, detail="Ese estudiante no tiene una alerta pendiente en el grupo.")
    s = AlertaSeguimiento(
        grupo_id=grupo.id,
        estudiante_id=datos.estudiante_id,
        atendido_por_id=usuario.id,
        motivos=",".join(sorted(m.codigo for m in vigente.motivos)),
        nota=datos.nota.strip(),
    )
    db.add(s)
    db.commit()
    return s


@router.get("/alertas/seguimientos", response_model=list[SeguimientoOut])
def seguimientos(usuario: Usuario = Depends(requiere_seguimiento), db: Session = Depends(get_db)):
    """Historial de atenciones registradas en los grupos visibles."""
    ids = [g.id for g in grupos_visibles(db, usuario)]
    if not ids:
        return []
    return list(db.scalars(select(AlertaSeguimiento).where(AlertaSeguimiento.grupo_id.in_(ids)).order_by(AlertaSeguimiento.creado_en.desc())))
