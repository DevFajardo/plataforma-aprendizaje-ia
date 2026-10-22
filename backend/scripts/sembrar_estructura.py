r"""Siembra la estructura académica institucional de ejemplo (Sprint 6). Es idempotente: solo añade lo que falta.

Uso (desde la carpeta backend):
    .\.venv\Scripts\python.exe scripts\sembrar_estructura.py

Crea: Facultad de Ingeniería > programa «Ingeniería de Sistemas y Computación» con 4 asignaturas y 5 resultados de
aprendizaje de EJEMPLO (marcados así en su descripción; reemplázalos por los reales del programa desde /admin),
las cuentas coordinador@demo.com y admin@demo.com (clave Demo12345) y un grupo del docente demo con el
estudiante demo matriculado. No toca datos existentes ni llama a ningún servicio de IA.
"""
import sys
from pathlib import Path

# Evita caracteres rotos en consolas de Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Permite ejecutar el script directamente: añade backend/ al path de importación
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal, crear_tablas  # noqa: E402
from app.modelos import (  # noqa: E402
    Asignatura,
    Facultad,
    Grupo,
    Matricula,
    Programa,
    ResultadoAprendizaje,
    Usuario,
    ahora,
    generar_codigo,
)
from app.seguridad import hashear_password  # noqa: E402

CLAVE_DEMO = "Demo12345"
FACULTAD = "Facultad de Ingeniería"
PROGRAMA = ("Ingeniería de Sistemas y Computación", "ISC")
PERIODO = "2026-2"

# (código, nombre, semestre, códigos de RA que aporta)
ASIGNATURAS = [
    ("POO101", "Programación Orientada a Objetos", 2, ["RA1", "RA2"]),
    ("ED101", "Estructuras de Datos", 3, ["RA1", "RA3"]),
    ("BD101", "Bases de Datos", 4, ["RA2", "RA4"]),
    ("IS201", "Ingeniería de Software", 5, ["RA4", "RA5"]),
]
RESULTADOS = [
    ("RA1", "Aplica principios de programación y algoritmos para resolver problemas computacionales (ejemplo)."),
    ("RA2", "Modela y construye soluciones de software con paradigmas y buenas prácticas de diseño (ejemplo)."),
    ("RA3", "Selecciona y utiliza estructuras de datos adecuadas según la eficiencia requerida (ejemplo)."),
    ("RA4", "Diseña, consulta y administra bases de datos que respaldan sistemas de información (ejemplo)."),
    ("RA5", "Participa en el ciclo de vida del software trabajando en equipo y con criterios de calidad (ejemplo)."),
]
USUARIOS = [
    ("Docente Demo", "docente@demo.com", "docente"),
    ("Estudiante Demo", "estudiante@demo.com", "estudiante"),
    ("Coordinador Demo", "coordinador@demo.com", "coordinador"),
    ("Administrador Demo", "admin@demo.com", "admin"),
]


def _usuario(db, nombre: str, email: str, rol: str) -> Usuario:
    u = db.scalar(select(Usuario).where(Usuario.email == email))
    if u:
        print(f"Ya existe: {email}")
        return u
    u = Usuario(
        nombre=nombre, email=email, password_hash=hashear_password(CLAVE_DEMO), rol=rol,
        acepta_tratamiento_datos=True, consentimiento_investigacion=True, consentimiento_fecha=ahora(),
    )
    db.add(u)
    db.flush()
    print(f"Creado: {email} ({rol}) / {CLAVE_DEMO}")
    return u


def main() -> None:
    crear_tablas()
    with SessionLocal() as db:
        fac = db.scalar(select(Facultad).where(Facultad.nombre == FACULTAD))
        if fac is None:
            fac = Facultad(nombre=FACULTAD)
            db.add(fac)
            db.flush()
            print(f"Creada: {FACULTAD}")

        prog = db.scalar(select(Programa).where(Programa.codigo == PROGRAMA[1]))
        if prog is None:
            prog = Programa(facultad_id=fac.id, nombre=PROGRAMA[0], codigo=PROGRAMA[1])
            db.add(prog)
            db.flush()
            print(f"Creado el programa: {PROGRAMA[0]}")

        ras: dict[str, ResultadoAprendizaje] = {}
        for codigo, descripcion in RESULTADOS:
            ra = db.scalar(select(ResultadoAprendizaje).where(ResultadoAprendizaje.programa_id == prog.id, ResultadoAprendizaje.codigo == codigo))
            if ra is None:
                ra = ResultadoAprendizaje(programa_id=prog.id, codigo=codigo, descripcion=descripcion)
                db.add(ra)
                db.flush()
                print(f"Creado el resultado de aprendizaje {codigo}")
            ras[codigo] = ra

        asignaturas: dict[str, Asignatura] = {}
        for codigo, nombre, semestre, codigos_ra in ASIGNATURAS:
            a = db.scalar(select(Asignatura).where(Asignatura.programa_id == prog.id, Asignatura.codigo == codigo))
            if a is None:
                a = Asignatura(programa_id=prog.id, nombre=nombre, codigo=codigo, semestre=semestre, resultados=[ras[c] for c in codigos_ra])
                db.add(a)
                db.flush()
                print(f"Creada la asignatura {nombre}")
            asignaturas[codigo] = a

        usuarios = {email: _usuario(db, nombre, email, rol) for nombre, email, rol in USUARIOS}
        coordinador = usuarios["coordinador@demo.com"]
        if coordinador.programa_id is None:
            coordinador.programa_id = prog.id
            print("Programa asignado al coordinador demo")

        docente, estudiante = usuarios["docente@demo.com"], usuarios["estudiante@demo.com"]
        grupo = db.scalar(select(Grupo).where(Grupo.asignatura_id == asignaturas["BD101"].id, Grupo.docente_id == docente.id, Grupo.periodo == PERIODO))
        if grupo is None:
            while True:
                codigo = generar_codigo()
                if not db.scalar(select(Grupo.id).where(Grupo.codigo_ingreso == codigo)):
                    break
            grupo = Grupo(asignatura_id=asignaturas["BD101"].id, docente_id=docente.id, periodo=PERIODO, nombre="Grupo A", codigo_ingreso=codigo)
            db.add(grupo)
            db.flush()
            print(f"Creado el grupo «Grupo A» ({PERIODO})")
        if not db.scalar(select(Matricula.id).where(Matricula.grupo_id == grupo.id, Matricula.estudiante_id == estudiante.id)):
            db.add(Matricula(grupo_id=grupo.id, estudiante_id=estudiante.id))
            print("Estudiante demo matriculado en el grupo")
        db.commit()
        print(f"Código de ingreso del grupo demo: {grupo.codigo_ingreso}")


if __name__ == "__main__":
    main()
