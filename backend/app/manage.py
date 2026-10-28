"""Administración: python -m app.manage create-professional --email X --name "Nombre" """
import argparse
import getpass
import os

from sqlalchemy import select

from .db import SessionLocal
from .models import Professional
from .security import hash_password


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create-professional")
    c.add_argument("--email", required=True)
    c.add_argument("--name", required=True)
    c.add_argument("--password-env", help="Leer la contraseña de esta variable de entorno (automatización)")
    c.add_argument("--if-missing", action="store_true", help="No fallar si el correo ya existe")
    a = ap.parse_args(argv)
    if a.cmd == "create-professional":
        if a.password_env:
            pw = os.environ.get(a.password_env, "")
            if len(pw) < 10:
                raise SystemExit("Contraseña inválida en la variable indicada")
        else:
            pw = getpass.getpass("Contraseña (mín. 10 caracteres): ")
            if len(pw) < 10 or pw != getpass.getpass("Repetir: "):
                raise SystemExit("Contraseña inválida o no coincide")
        with SessionLocal() as db:
            email = a.email.lower().strip()
            if db.execute(select(Professional).where(Professional.email == email)).scalar_one_or_none():
                if a.if_missing:
                    print("Profesional ya existente")
                    return
                raise SystemExit("Ya existe ese correo")
            db.add(Professional(email=email, full_name=a.name, password_hash=hash_password(pw)))
            db.commit()
        print("Profesional creado")


if __name__ == "__main__":
    main()
