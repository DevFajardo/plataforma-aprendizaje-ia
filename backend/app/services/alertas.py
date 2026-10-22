"""Alertas tempranas explicables, calculadas al vuelo (no se almacenan; solo se guarda su atención).

Reglas por estudiante matriculado en un grupo:
- inactividad:       sin actividad (intentos) hace 14 días o más (desde la matrícula si nunca ha hecho un intento).
- bajo_promedio:     promedio de sus intentos INICIALES en los cuestionarios del grupo menor a 60 %.
- repasos_vencidos:  2 o más repasos diferidos vencidos sin hacer.
- caida:             caída de 20 puntos porcentuales o más entre sus dos últimos intentos del grupo.
Nivel «alto» con 2 o más motivos; «medio» con uno. Una alerta atendida no se muestra de nuevo hasta que
aparezca un motivo que no estaba en la atención más reciente.
"""
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos import AlertaSeguimiento, Cuestionario, Grupo, Intento, Matricula, Repaso, Usuario, ahora, como_utc
from app.schemas_academico import AlertaOut, MotivoAlerta

DIAS_INACTIVIDAD = 14
UMBRAL_PROMEDIO = 60.0
REPASOS_VENCIDOS = 2
CAIDA_PUNTOS = 20.0


def _pct(i: Intento) -> float:
    return 100 * i.puntaje / i.total if i.total else 0.0


def calcular_alertas(db: Session, grupos: list[Grupo], hoy: datetime | None = None, incluir_atendidas: bool = False) -> list[AlertaOut]:
    hoy = hoy or ahora()
    if not grupos:
        return []
    ids_grupos = [g.id for g in grupos]
    matriculas = db.execute(
        select(Matricula, Usuario).join(Usuario, Usuario.id == Matricula.estudiante_id).where(Matricula.grupo_id.in_(ids_grupos))
    ).all()
    if not matriculas:
        return []
    ids_est = {u.id for _, u in matriculas}

    cuestionarios_de: dict[int, set[int]] = defaultdict(set)
    for cid, gid in db.execute(select(Cuestionario.id, Cuestionario.grupo_id).where(Cuestionario.grupo_id.in_(ids_grupos))):
        cuestionarios_de[gid].add(cid)

    intentos_de: dict[int, list[Intento]] = defaultdict(list)
    for i in db.scalars(select(Intento).where(Intento.usuario_id.in_(ids_est)).order_by(Intento.creado_en, Intento.id)):
        intentos_de[i.usuario_id].append(i)
    vencidos_de: dict[int, int] = defaultdict(int)
    for r in db.scalars(select(Repaso).where(Repaso.usuario_id.in_(ids_est), Repaso.completado_intento_id.is_(None))):
        if como_utc(r.disponible_desde) <= hoy:
            vencidos_de[r.usuario_id] += 1

    # Última atención registrada por (grupo, estudiante)
    ultima_atencion: dict[tuple[int, int], set[str]] = {}
    for s in db.scalars(select(AlertaSeguimiento).where(AlertaSeguimiento.grupo_id.in_(ids_grupos)).order_by(AlertaSeguimiento.creado_en, AlertaSeguimiento.id)):
        ultima_atencion[(s.grupo_id, s.estudiante_id)] = set(filter(None, s.motivos.split(",")))

    por_id = {g.id: g for g in grupos}
    salida: list[AlertaOut] = []
    for m, u in matriculas:
        g = por_id[m.grupo_id]
        todos = intentos_de.get(u.id, [])
        en_grupo = [i for i in todos if i.cuestionario_id in cuestionarios_de[g.id] and i.finalizado]
        motivos: list[MotivoAlerta] = []

        # 1. Inactividad
        referencia = como_utc(m.creado_en)
        if todos:
            referencia = max(referencia, como_utc(todos[-1].creado_en))
        dias = (hoy - referencia).days
        if dias >= DIAS_INACTIVIDAD:
            motivos.append(MotivoAlerta(codigo="inactividad", texto=f"Sin actividad desde hace {dias} días."))

        # 2. Bajo promedio en intentos iniciales
        iniciales = [_pct(i) for i in en_grupo if i.tipo == "inicial"]
        if iniciales:
            promedio = sum(iniciales) / len(iniciales)
            if promedio < UMBRAL_PROMEDIO:
                motivos.append(MotivoAlerta(codigo="bajo_promedio", texto=f"Promedio de intentos iniciales de {promedio:.0f} %, por debajo de {UMBRAL_PROMEDIO:.0f} %."))

        # 3. Repasos vencidos sin hacer
        if vencidos_de.get(u.id, 0) >= REPASOS_VENCIDOS:
            motivos.append(MotivoAlerta(codigo="repasos_vencidos", texto=f"Tiene {vencidos_de[u.id]} repasos vencidos sin hacer."))

        # 4. Caída entre los dos últimos intentos
        if len(en_grupo) >= 2:
            anterior, ultimo = _pct(en_grupo[-2]), _pct(en_grupo[-1])
            if anterior - ultimo >= CAIDA_PUNTOS:
                motivos.append(MotivoAlerta(codigo="caida", texto=f"Su último intento ({ultimo:.0f} %) bajó {anterior - ultimo:.0f} puntos respecto al anterior ({anterior:.0f} %)."))

        if not motivos:
            continue
        codigos = {x.codigo for x in motivos}
        atendida = (g.id, u.id) in ultima_atencion and codigos <= ultima_atencion[(g.id, u.id)]
        if atendida and not incluir_atendidas:
            continue
        salida.append(AlertaOut(
            grupo_id=g.id, grupo=f"{g.nombre} ({g.periodo})", asignatura=g.asignatura.nombre,
            estudiante_id=u.id, nombre=u.nombre, email=u.email,
            nivel="alto" if len(motivos) >= 2 else "medio", motivos=motivos,
        ))
    salida.sort(key=lambda a: (a.nivel != "alto", -len(a.motivos), a.nombre))
    return salida
