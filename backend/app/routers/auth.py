"""Registro, inicio de sesión, datos de la cuenta y derechos del titular (Ley 1581 de 2012)."""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.modelos import (
    AlertaSeguimiento,
    Cuestionario,
    Grupo,
    Intento,
    Matricula,
    Repaso,
    RespuestaSUS,
    Tarea,
    Usuario,
    Video,
    ahora,
)
from app.routers import procesar
from app.routers.cuestionarios import borrar_cuestionario
from app.schemas_api import CuentaEditarIn, EliminarCuentaIn, LoginIn, RegistroIn, TokenOut, UsuarioOut
from app.seguridad import crear_token, hashear_password, usuario_actual, verificar_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/registro", response_model=TokenOut, status_code=201)
def registro(datos: RegistroIn, db: Session = Depends(get_db)):
    email = datos.email.lower()
    if db.scalar(select(Usuario).where(Usuario.email == email)):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo.")
    usuario = Usuario(
        nombre=datos.nombre.strip(),
        email=email,
        password_hash=hashear_password(datos.password),
        rol=datos.rol,
        acepta_tratamiento_datos=True,
        consentimiento_investigacion=datos.consentimiento_investigacion,
        consentimiento_fecha=ahora(),
    )
    db.add(usuario)
    db.commit()
    return TokenOut(token=crear_token(usuario.id), usuario=UsuarioOut.model_validate(usuario))


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == datos.email.lower()))
    if not usuario or not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    return TokenOut(token=crear_token(usuario.id), usuario=UsuarioOut.model_validate(usuario))


@router.get("/yo", response_model=UsuarioOut)
def yo(usuario: Usuario = Depends(usuario_actual)):
    return usuario


@router.patch("/cuenta", response_model=UsuarioOut)
def editar_cuenta(datos: CuentaEditarIn, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Rectificación y actualización de datos: nombre, contraseña (pide la actual) y consentimientos."""
    if datos.password_nueva is not None:
        if not datos.password_actual or not verificar_password(datos.password_actual, usuario.password_hash):
            raise HTTPException(status_code=400, detail="La contraseña actual no es correcta.")
        usuario.password_hash = hashear_password(datos.password_nueva)
    if datos.nombre is not None:
        usuario.nombre = datos.nombre.strip() or usuario.nombre
    if datos.consentimiento_investigacion is not None:
        usuario.consentimiento_investigacion = datos.consentimiento_investigacion
        usuario.consentimiento_fecha = ahora()
    if datos.acepta_tratamiento_datos is True and not usuario.acepta_tratamiento_datos:
        usuario.acepta_tratamiento_datos = True
        usuario.consentimiento_fecha = ahora()
    db.commit()
    return usuario


@router.get("/mis-datos")
def mis_datos(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Derecho de acceso: todos los datos personales que la plataforma guarda sobre el usuario."""
    cuestionarios = db.scalars(select(Cuestionario).where(Cuestionario.creador_id == usuario.id)).all()
    intentos = db.scalars(select(Intento).where(Intento.usuario_id == usuario.id).order_by(Intento.creado_en)).all()
    repasos = db.scalars(select(Repaso).where(Repaso.usuario_id == usuario.id)).all()
    encuesta = db.scalar(select(RespuestaSUS).where(RespuestaSUS.usuario_id == usuario.id))
    return {
        "generado_en": ahora().isoformat(),
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol,
            "creado_en": usuario.creado_en.isoformat(),
            "acepta_tratamiento_datos": usuario.acepta_tratamiento_datos,
            "consentimiento_investigacion": usuario.consentimiento_investigacion,
            "consentimiento_fecha": usuario.consentimiento_fecha.isoformat() if usuario.consentimiento_fecha else None,
        },
        "cuestionarios": [
            {
                "id": c.id,
                "titulo": c.titulo,
                "resumen": c.resumen,
                "ideas_clave": json.loads(c.ideas_clave_json),
                "modo": c.modo,
                "publicado": c.publicado,
                "repaso_dias": c.repaso_dias,
                "num_preguntas": c.num_preguntas,
                "url_video": c.video.url,
                "segundos_edicion": c.segundos_edicion,
                "estimacion_manual_min": c.estimacion_manual_min,
                "creado_en": c.creado_en.isoformat(),
            }
            for c in cuestionarios
        ],
        "intentos": [
            {
                "id": i.id,
                "cuestionario_id": i.cuestionario_id,
                "tipo": i.tipo,
                "finalizado": i.finalizado,
                "puntaje": i.puntaje,
                "total": i.total,
                "respuestas": json.loads(i.respuestas_json),
                "creado_en": i.creado_en.isoformat(),
            }
            for i in intentos
        ],
        "repasos": [
            {
                "cuestionario_id": r.cuestionario_id,
                "disponible_desde": r.disponible_desde.isoformat(),
                "completado": r.completado_intento_id is not None,
            }
            for r in repasos
        ],
        "encuesta": (
            {
                "respuestas": json.loads(encuesta.respuestas_json),
                "puntaje_sus": encuesta.puntaje_sus,
                "comentario": encuesta.comentario,
                "creado_en": encuesta.creado_en.isoformat(),
            }
            if encuesta
            else None
        ),
    }


@router.delete("/cuenta", status_code=204)
def eliminar_cuenta(datos: EliminarCuentaIn, usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Derecho de supresión: borra la cuenta y todo lo asociado (intentos, repasos, encuesta, tareas,
    cuestionarios propios con sus preguntas y los archivos subidos)."""
    if not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña no es correcta.")

    subidas = [a for a in db.scalars(select(Tarea.archivo).where(Tarea.usuario_id == usuario.id)) if a]
    db.execute(delete(Tarea).where(Tarea.usuario_id == usuario.id))
    archivos = []
    for c in db.scalars(select(Cuestionario).where(Cuestionario.creador_id == usuario.id)).all():
        ruta = borrar_cuestionario(db, c)
        if ruta:
            archivos.append(ruta)
    db.flush()
    db.execute(delete(Repaso).where(Repaso.usuario_id == usuario.id))
    db.execute(delete(Intento).where(Intento.usuario_id == usuario.id))
    db.execute(delete(RespuestaSUS).where(RespuestaSUS.usuario_id == usuario.id))
    # Estructura académica: matrículas, alertas y los grupos que dictaba (docente)
    ids_grupos = list(db.scalars(select(Grupo.id).where(Grupo.docente_id == usuario.id)))
    if ids_grupos:
        db.execute(update(Cuestionario).where(Cuestionario.grupo_id.in_(ids_grupos)).values(grupo_id=None))
        db.execute(delete(AlertaSeguimiento).where(AlertaSeguimiento.grupo_id.in_(ids_grupos)))
        db.execute(delete(Matricula).where(Matricula.grupo_id.in_(ids_grupos)))
        db.execute(delete(Grupo).where(Grupo.id.in_(ids_grupos)))
    db.execute(delete(AlertaSeguimiento).where(
        (AlertaSeguimiento.estudiante_id == usuario.id) | (AlertaSeguimiento.atendido_por_id == usuario.id)))
    db.execute(delete(Matricula).where(Matricula.estudiante_id == usuario.id))
    db.delete(usuario)
    db.commit()
    for ruta in archivos:
        ruta.unlink(missing_ok=True)
    # Archivos subidos que quedaron sin cuestionario (tareas fallidas o en curso) y que ningún video usa
    for nombre in subidas:
        if not db.scalar(select(Video.id).where(Video.archivo == nombre)):
            (procesar.CARPETA_SUBIDAS / Path(nombre).name).unlink(missing_ok=True)
