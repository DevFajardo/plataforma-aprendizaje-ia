r"""Crea las cuentas demo (docente y estudiante) si no existen. Es idempotente.

Uso (desde la carpeta backend):
    .\.venv\Scripts\python.exe scripts\crear_demo.py

No genera cuestionarios (eso consume cuota de IA): se generan desde la aplicación.
"""
import sys
from pathlib import Path

# Permite ejecutar el script directamente: añade backend/ al path de importación
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal, crear_tablas  # noqa: E402
from app.modelos import Usuario, ahora  # noqa: E402
from app.seguridad import hashear_password  # noqa: E402

CLAVE_DEMO = "Demo12345"
USUARIOS_DEMO = [
    ("Docente Demo", "docente@demo.com", "docente"),
    ("Estudiante Demo", "estudiante@demo.com", "estudiante"),
]


def main() -> None:
    crear_tablas()
    with SessionLocal() as db:
        for nombre, email, rol in USUARIOS_DEMO:
            existente = db.scalar(select(Usuario).where(Usuario.email == email))
            if existente:
                if not (existente.acepta_tratamiento_datos and existente.consentimiento_investigacion):
                    existente.acepta_tratamiento_datos = True
                    existente.consentimiento_investigacion = True
                    existente.consentimiento_fecha = ahora()
                    db.commit()
                    print(f"Ya existía: {email} (consentimientos registrados)")
                else:
                    print(f"Ya existe: {email}")
                continue
            db.add(
                Usuario(
                    nombre=nombre,
                    email=email,
                    password_hash=hashear_password(CLAVE_DEMO),
                    rol=rol,
                    # Las cuentas demo aceptan la política de datos y el estudio (Ley 1581 de 2012)
                    acepta_tratamiento_datos=True,
                    consentimiento_investigacion=True,
                    consentimiento_fecha=ahora(),
                )
            )
            db.commit()
            print(f"Creado: {email} ({rol}) / {CLAVE_DEMO}")


if __name__ == "__main__":
    main()
