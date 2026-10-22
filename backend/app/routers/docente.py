"""Funciones del docente: publicar/compartir, editar cuestionarios y ver resultados."""
import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import Cuestionario, Grupo, Intento, Pregunta, Usuario, ahora, generar_codigo
from app.schemas_api import (
    CompartidoOut,
    CuestionarioEditarIn,
    DuplicarIn,
    EstudianteGanancia,
    EstudianteRetencion,
    GananciaAprendizaje,
    IntentoResultado,
    PreguntaIn,
    PreguntaOut,
    PreguntaResultado,
    PublicarIn,
    ReordenarIn,
    RespuestaAbiertaOut,
    ResultadosOut,
    RetencionOut,
    TiempoEdicionIn,
)
from app.seguridad import requiere_docente, usuario_actual
from app.services.estadistica import datos_por_estudiante
from app.services.notificaciones import notificar_publicacion

router = APIRouter(prefix="/api", tags=["docente"])


def _propio(db: Session, cuestionario_id: int, docente: Usuario) -> Cuestionario:
    c = db.get(Cuestionario, cuestionario_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Cuestionario no encontrado.")
    if c.creador_id != docente.id:
        raise HTTPException(status_code=403, detail="Solo el creador del cuestionario puede hacer esto.")
    return c


def _pregunta_propia(db: Session, pregunta_id: int, docente: Usuario) -> Pregunta:
    p = db.get(Pregunta, pregunta_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada.")
    _propio(db, p.cuestionario_id, docente)
    return p


def _a_salida(p: Pregunta) -> PreguntaOut:
    return PreguntaOut(
        id=p.id,
        orden=p.orden,
        tipo=p.tipo,
        enunciado=p.enunciado,
        opciones=json.loads(p.opciones_json),
        marca_tiempo=p.marca_tiempo,
        respuesta_correcta=p.respuesta_correcta,
        explicacion=p.explicacion,
        ra_id=p.ra_id,
        nivel_bloom=p.nivel_bloom,
    )


def grupo_propio(db: Session, grupo_id: int, docente: Usuario) -> Grupo:
    g = db.get(Grupo, grupo_id)
    if g is None:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")
    if g.docente_id != docente.id:
        raise HTTPException(status_code=403, detail="Ese grupo pertenece a otro docente.")
    return g


def _ras_permitidos(c: Cuestionario) -> set[int]:
    """Resultados de aprendizaje que se pueden asociar a las preguntas: los de la asignatura del grupo."""
    return {r.id for r in c.grupo.asignatura.resultados} if c.grupo_id and c.grupo else set()


def _validar_ra(c: Cuestionario, ra_id: int | None) -> None:
    if ra_id is None:
        return
    if not c.grupo_id:
        raise HTTPException(status_code=400, detail="Asigna primero el cuestionario a un grupo para elegir un resultado de aprendizaje.")
    if ra_id not in _ras_permitidos(c):
        raise HTTPException(status_code=400, detail="Ese resultado de aprendizaje no pertenece a la asignatura del grupo.")


def _aplicar(p: Pregunta, datos: PreguntaIn) -> None:
    p.tipo = datos.tipo
    p.enunciado = datos.enunciado
    p.opciones_json = json.dumps(datos.opciones, ensure_ascii=False)
    p.respuesta_correcta = datos.respuesta_correcta
    p.explicacion = datos.explicacion
    p.marca_tiempo = datos.marca_tiempo
    p.ra_id = datos.ra_id
    p.nivel_bloom = datos.nivel_bloom


# ---------- Publicar y compartir ----------

def _asignar_grupo(c: Cuestionario, grupo_id: int | None) -> None:
    """Asigna (o quita) el grupo y limpia los RA de las preguntas que ya no correspondan a la asignatura."""
    if c.grupo_id == grupo_id:
        return
    c.grupo_id = grupo_id
    for p in c.preguntas:
        p.ra_id = None


@router.post("/cuestionarios/{cuestionario_id}/publicar")
def publicar(
    cuestionario_id: int,
    datos: PublicarIn,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    c = _propio(db, cuestionario_id, docente)
    if datos.grupo_id is not None:
        grupo_propio(db, datos.grupo_id, docente)
        _asignar_grupo(c, datos.grupo_id)
    c.publicado = datos.publicado
    if datos.publicado and c.publicado_en is None:
        c.publicado_en = ahora()  # primera publicación
    if datos.estimacion_manual_min is not None:
        c.estimacion_manual_min = datos.estimacion_manual_min
    notificar_publicacion(db, c)
    db.commit()
    return {"publicado": c.publicado, "codigo_compartir": c.codigo_compartir}


@router.post("/cuestionarios/{cuestionario_id}/tiempo-edicion")
def registrar_tiempo_edicion(
    cuestionario_id: int,
    datos: TiempoEdicionIn,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    """Suma el tiempo activo (pestaña visible) de una sesión de edición; máximo 4 h por llamada."""
    c = _propio(db, cuestionario_id, docente)
    c.segundos_edicion = (c.segundos_edicion or 0) + datos.segundos
    db.commit()
    return {"segundos_edicion": c.segundos_edicion}


@router.post("/cuestionarios/{cuestionario_id}/duplicar", status_code=201)
def duplicar(
    cuestionario_id: int,
    datos: DuplicarIn,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    """Copia el cuestionario (con preguntas) como borrador, p. ej. para crear la versión del grupo control."""
    c = _propio(db, cuestionario_id, docente)
    copia = Cuestionario(
        video_id=c.video_id,
        creador_id=c.creador_id,
        titulo=(datos.titulo or f"{c.titulo} ({'grupo control' if datos.modo == 'control' else 'copia'})").strip(),
        resumen=c.resumen,
        ideas_clave_json=c.ideas_clave_json,
        proveedor_ia=c.proveedor_ia,
        num_preguntas=c.num_preguntas,
        publicado=False,
        modo=datos.modo,
        repaso_dias=c.repaso_dias,
        grupo_id=c.grupo_id,
        preguntas=[
            Pregunta(
                orden=p.orden,
                tipo=p.tipo,
                enunciado=p.enunciado,
                opciones_json=p.opciones_json,
                respuesta_correcta=p.respuesta_correcta,
                explicacion=p.explicacion,
                marca_tiempo=p.marca_tiempo,
                ra_id=p.ra_id,
                nivel_bloom=p.nivel_bloom,
            )
            for p in c.preguntas
        ],
    )
    while True:  # el código debe ser único
        copia.codigo_compartir = generar_codigo()
        if not db.scalar(select(Cuestionario.id).where(Cuestionario.codigo_compartir == copia.codigo_compartir)):
            break
    db.add(copia)
    db.commit()
    return {"id": copia.id, "titulo": copia.titulo, "modo": copia.modo, "codigo_compartir": copia.codigo_compartir}


@router.get("/compartido/{codigo}", response_model=CompartidoOut)
def resolver_codigo(codigo: str, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    c = db.scalar(select(Cuestionario).where(Cuestionario.codigo_compartir == codigo.strip().upper()))
    if c is None:
        raise HTTPException(status_code=404, detail="No existe ningún cuestionario con ese código. Revisa que esté bien escrito.")
    if not c.publicado:
        raise HTTPException(
            status_code=404,
            detail="Ese cuestionario existe pero el docente aún no lo ha publicado. Pídele que lo publique e inténtalo de nuevo.",
        )
    creador = db.get(Usuario, c.creador_id)
    return CompartidoOut(cuestionario_id=c.id, titulo=c.titulo, creador=creador.nombre if creador else "Docente")


# ---------- Edición ----------

@router.patch("/cuestionarios/{cuestionario_id}")
def editar_cuestionario(
    cuestionario_id: int,
    datos: CuestionarioEditarIn,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    c = _propio(db, cuestionario_id, docente)
    if datos.titulo is not None:
        c.titulo = datos.titulo.strip()
    if datos.resumen is not None:
        c.resumen = datos.resumen.strip()
    if datos.ideas_clave is not None:
        c.ideas_clave_json = json.dumps(datos.ideas_clave, ensure_ascii=False)
    # Estos dos admiten null explícito (quitar el valor)
    if "repaso_dias" in datos.model_fields_set:
        c.repaso_dias = datos.repaso_dias
    if "estimacion_manual_min" in datos.model_fields_set:
        c.estimacion_manual_min = datos.estimacion_manual_min
    if "grupo_id" in datos.model_fields_set:
        if datos.grupo_id is not None:
            grupo_propio(db, datos.grupo_id, docente)
        _asignar_grupo(c, datos.grupo_id)
    db.commit()
    return {
        "titulo": c.titulo,
        "resumen": c.resumen,
        "ideas_clave": json.loads(c.ideas_clave_json),
        "repaso_dias": c.repaso_dias,
        "estimacion_manual_min": c.estimacion_manual_min,
        "grupo_id": c.grupo_id,
    }


@router.get("/cuestionarios/{cuestionario_id}/ras")
def ras_del_cuestionario(
    cuestionario_id: int,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    """Resultados de aprendizaje elegibles para las preguntas (los de la asignatura del grupo del cuestionario)."""
    c = _propio(db, cuestionario_id, docente)
    if not c.grupo_id:
        return []
    return [
        {"id": r.id, "codigo": r.codigo, "descripcion": r.descripcion}
        for r in sorted(c.grupo.asignatura.resultados, key=lambda r: r.codigo)
    ]


@router.put("/preguntas/{pregunta_id}", response_model=PreguntaOut)
def editar_pregunta(
    pregunta_id: int,
    datos: PreguntaIn,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    p = _pregunta_propia(db, pregunta_id, docente)
    _validar_ra(p.cuestionario, datos.ra_id)
    _aplicar(p, datos)
    db.commit()
    return _a_salida(p)


@router.post("/cuestionarios/{cuestionario_id}/preguntas", response_model=PreguntaOut, status_code=201)
def agregar_pregunta(
    cuestionario_id: int,
    datos: PreguntaIn,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    c = _propio(db, cuestionario_id, docente)
    _validar_ra(c, datos.ra_id)
    p = Pregunta(cuestionario_id=c.id, orden=max((x.orden for x in c.preguntas), default=-1) + 1)
    _aplicar(p, datos)
    db.add(p)
    db.flush()
    c.num_preguntas = len(c.preguntas) + 1
    db.commit()
    return _a_salida(p)


@router.delete("/preguntas/{pregunta_id}", status_code=204)
def eliminar_pregunta(
    pregunta_id: int,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    p = _pregunta_propia(db, pregunta_id, docente)
    c = p.cuestionario
    db.delete(p)
    db.flush()
    restantes = db.scalars(
        select(Pregunta).where(Pregunta.cuestionario_id == c.id).order_by(Pregunta.orden)
    ).all()
    for i, q in enumerate(restantes):
        q.orden = i
    c.num_preguntas = len(restantes)
    db.commit()


@router.post("/cuestionarios/{cuestionario_id}/reordenar", response_model=list[PreguntaOut])
def reordenar(
    cuestionario_id: int,
    datos: ReordenarIn,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    c = _propio(db, cuestionario_id, docente)
    por_id = {p.id: p for p in c.preguntas}
    if sorted(datos.ids) != sorted(por_id):
        raise HTTPException(status_code=400, detail="La lista debe contener exactamente las preguntas del cuestionario.")
    for i, pid in enumerate(datos.ids):
        por_id[pid].orden = i
    db.commit()
    return [_a_salida(por_id[pid]) for pid in datos.ids]


# ---------- Resultados ----------

def _calcular_ganancia(filas: list[tuple[Intento, Usuario]]) -> GananciaAprendizaje:
    """Pre-test/post-test: por estudiante con >= 2 intentos, compara el primero con el último."""
    por_usuario: dict[int, list[tuple[Intento, Usuario]]] = {}
    for i, u in sorted(filas, key=lambda f: (f[0].creado_en, f[0].id)):
        por_usuario.setdefault(u.id, []).append((i, u))

    def pct(i: Intento) -> float:
        return 100 * i.puntaje / i.total if i.total else 0.0

    detalle: list[EstudianteGanancia] = []
    for lista in por_usuario.values():
        if len(lista) < 2:
            continue
        primero, ultimo = pct(lista[0][0]), pct(lista[-1][0])
        detalle.append(
            EstudianteGanancia(
                nombre=lista[0][1].nombre,
                email=lista[0][1].email,
                intentos=len(lista),
                primer_porcentaje=round(primero, 1),
                ultimo_porcentaje=round(ultimo, 1),
                diferencia=round(ultimo - primero, 1),
            )
        )
    if not detalle:
        return GananciaAprendizaje(estudiantes=0)
    media_primero = sum(d.primer_porcentaje for d in detalle) / len(detalle)
    media_ultimo = sum(d.ultimo_porcentaje for d in detalle) / len(detalle)
    return GananciaAprendizaje(
        estudiantes=len(detalle),
        promedio_primer_intento=round(media_primero, 1),
        promedio_ultimo_intento=round(media_ultimo, 1),
        diferencia_puntos=round(media_ultimo - media_primero, 1),
        detalle=detalle,
    )


def _calcular_retencion(db: Session, c: Cuestionario) -> RetencionOut:
    """Retención: intento inicial vs. intento diferido de los estudiantes que hicieron ambos."""
    completos = [d for d in datos_por_estudiante(db, c) if d.inicial is not None and d.diferido is not None]
    if not completos:
        return RetencionOut(repaso_dias=c.repaso_dias, estudiantes=0)
    media_inicial = sum(d.inicial for d in completos) / len(completos)
    media_diferido = sum(d.diferido for d in completos) / len(completos)
    return RetencionOut(
        repaso_dias=c.repaso_dias,
        estudiantes=len(completos),
        promedio_inicial=round(media_inicial, 1),
        promedio_diferido=round(media_diferido, 1),
        retencion_pct=round(100 * media_diferido / media_inicial, 1) if media_inicial > 0 else None,
        diferencia_puntos=round(media_diferido - media_inicial, 1),
        detalle=[
            EstudianteRetencion(
                nombre=d.usuario.nombre,
                email=d.usuario.email,
                inicial=round(d.inicial, 1),
                diferido=round(d.diferido, 1),
                retencion=round(d.retencion, 1) if d.retencion is not None else None,
                diferencia=round(d.diferido - d.inicial, 1),
            )
            for d in completos
        ],
    )


def _calcular_resultados(db: Session, c: Cuestionario) -> ResultadosOut:
    filas = db.execute(
        select(Intento, Usuario)
        .join(Usuario, Usuario.id == Intento.usuario_id)
        .where(Intento.cuestionario_id == c.id, Intento.finalizado.is_(True))
        .order_by(Intento.creado_en.desc())
    ).all()

    intentos: list[IntentoResultado] = []
    por_pregunta: dict[int, list[tuple[str, dict]]] = {}
    for i, u in filas:
        intentos.append(
            IntentoResultado(
                intento_id=i.id,
                nombre=u.nombre,
                email=u.email,
                puntaje=i.puntaje,
                total=i.total,
                porcentaje=round(100 * i.puntaje / i.total, 1) if i.total else 0.0,
                fecha=i.creado_en,
                tipo=i.tipo or "inicial",
                consentimiento_investigacion=bool(u.consentimiento_investigacion),
            )
        )
        for r in json.loads(i.respuestas_json):
            por_pregunta.setdefault(r["pregunta_id"], []).append((u.nombre, r))

    preguntas: list[PreguntaResultado] = []
    ra_codigos = {r.id: r.codigo for r in c.grupo.asignatura.resultados} if c.grupo_id and c.grupo else {}
    for p in c.preguntas:
        resp = por_pregunta.get(p.id, [])
        if p.tipo == "abierta":
            preguntas.append(
                PreguntaResultado(
                    pregunta_id=p.id,
                    orden=p.orden,
                    tipo=p.tipo,
                    enunciado=p.enunciado,
                    num_respuestas=len(resp),
                    respuestas_abiertas=[RespuestaAbiertaOut(nombre=n, respuesta=r["respuesta"]) for n, r in resp],
                )
            )
        else:
            aciertos = sum(1 for _, r in resp if r.get("correcta") is True)
            preguntas.append(
                PreguntaResultado(
                    pregunta_id=p.id,
                    orden=p.orden,
                    tipo=p.tipo,
                    enunciado=p.enunciado,
                    num_respuestas=len(resp),
                    porcentaje_acierto=round(100 * aciertos / len(resp), 1) if resp else 0.0,
                    ra_codigo=ra_codigos.get(p.ra_id),
                    nivel_bloom=p.nivel_bloom,
                )
            )

    promedio = round(sum(x.porcentaje for x in intentos) / len(intentos), 1) if intentos else 0.0
    return ResultadosOut(
        titulo=c.titulo,
        modo=c.modo or "aprendizaje",
        total_intentos=len(intentos),
        estudiantes_unicos=len({u.id for _, u in filas}),
        promedio_porcentaje=promedio,
        intentos=intentos,
        preguntas=preguntas,
        # El intento diferido se analiza aparte (retención): no cuenta como "último intento"
        ganancia=_calcular_ganancia([(i, u) for i, u in filas if i.tipo != "diferido"]),
        retencion=_calcular_retencion(db, c),
    )


@router.get("/cuestionarios/{cuestionario_id}/resultados", response_model=ResultadosOut)
def resultados(
    cuestionario_id: int,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    return _calcular_resultados(db, _propio(db, cuestionario_id, docente))


def _celda_segura(valor: str) -> str:
    """Evita la inyección de fórmulas al abrir el CSV en Excel."""
    return "'" + valor if valor[:1] in ("=", "+", "-", "@") else valor


@router.get("/cuestionarios/{cuestionario_id}/resultados.csv")
def resultados_csv(
    cuestionario_id: int,
    docente: Usuario = Depends(requiere_docente),
    db: Session = Depends(get_db),
):
    r = _calcular_resultados(db, _propio(db, cuestionario_id, docente))
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(["Nombre", "Correo", "Puntaje", "Total", "Porcentaje", "Fecha (UTC)",
                "Tipo de intento", "Consentimiento investigación"])
    for i in r.intentos:
        w.writerow(
            [_celda_segura(i.nombre), _celda_segura(i.email), i.puntaje, i.total, i.porcentaje,
             i.fecha.strftime("%Y-%m-%d %H:%M"), i.tipo, "Sí" if i.consentimiento_investigacion else "No"]
        )
    g = r.ganancia
    w.writerow([])
    w.writerow(["Ganancia de aprendizaje (primer intento vs. último intento)"])
    w.writerow(["Estudiantes con 2 o más intentos", g.estudiantes])
    w.writerow(["Promedio del primer intento (%)", g.promedio_primer_intento if g.estudiantes else ""])
    w.writerow(["Promedio del último intento (%)", g.promedio_ultimo_intento if g.estudiantes else ""])
    w.writerow(["Diferencia (puntos porcentuales)", g.diferencia_puntos if g.estudiantes else ""])
    if g.detalle:
        w.writerow([])
        w.writerow(["Nombre", "Correo", "Intentos", "Primer intento (%)", "Último intento (%)", "Diferencia (puntos)"])
        for d in g.detalle:
            w.writerow([_celda_segura(d.nombre), _celda_segura(d.email), d.intentos,
                        d.primer_porcentaje, d.ultimo_porcentaje, d.diferencia])
    ret = r.retencion
    w.writerow([])
    w.writerow([f"Retención (intento inicial vs. intento diferido a {ret.repaso_dias} días)"
                if ret.repaso_dias else "Retención (intento inicial vs. intento diferido)"])
    w.writerow(["Estudiantes con intento inicial y diferido", ret.estudiantes])
    w.writerow(["Promedio inicial (%)", ret.promedio_inicial if ret.estudiantes else ""])
    w.writerow(["Promedio diferido (%)", ret.promedio_diferido if ret.estudiantes else ""])
    w.writerow(["Retención % (diferido / inicial x 100)", ret.retencion_pct if ret.retencion_pct is not None else ""])
    w.writerow(["Diferencia (puntos porcentuales)", ret.diferencia_puntos if ret.estudiantes else ""])
    if ret.detalle:
        w.writerow([])
        w.writerow(["Nombre", "Correo", "Inicial (%)", "Diferido (%)", "Retención (%)", "Diferencia (puntos)"])
        for d in ret.detalle:
            w.writerow([_celda_segura(d.nombre), _celda_segura(d.email), d.inicial, d.diferido,
                        d.retencion if d.retencion is not None else "", d.diferencia])
    contenido = "﻿" + salida.getvalue()  # BOM para que Excel muestre bien las tildes
    return Response(
        content=contenido.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="resultados_{cuestionario_id}.csv"'},
    )
