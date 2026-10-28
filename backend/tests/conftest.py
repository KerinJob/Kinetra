"""Pruebas del backend contra PostgreSQL real (base kinetra_test). Datos sintéticos únicamente."""
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import get_settings  # noqa: E402

_s = get_settings()
if not _s.test_database_url:
    pytest.skip("KINETRA_TEST_DATABASE_URL no configurada", allow_module_level=True)


@pytest.fixture(scope="session")
def tmp_storage(tmp_path_factory):
    return tmp_path_factory.mktemp("storage")


@pytest.fixture(scope="session", autouse=True)
def database(tmp_storage):
    from sqlalchemy import create_engine, text
    from alembic import command
    from alembic.config import Config

    eng = create_engine(_s.test_database_url)
    with eng.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    eng.dispose()
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "migrations"))
    cfg.attributes["url"] = _s.test_database_url
    command.upgrade(cfg, "head")

    _s.database_url = _s.test_database_url
    _s.storage_dir = tmp_storage
    from app import db
    db.init_engine(_s.test_database_url)
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def professional():
    from app.db import SessionLocal
    from app.models import Professional
    from app.security import hash_password
    with SessionLocal() as s:
        p = Professional(email="prueba@kinetra.local", full_name="Profesional de Prueba",
                         password_hash=hash_password("clave-de-prueba-123"))
        s.add(p)
        s.commit()
        return p.id


@pytest.fixture
def auth_client(client, professional):
    r = client.post("/api/auth/login", json={"email": "prueba@kinetra.local", "password": "clave-de-prueba-123"})
    assert r.status_code == 200
    return client


@pytest.fixture(scope="session")
def synthetic_video(tmp_path_factory) -> Path:
    """Video gris sin personas generado en la prueba (no es un video de paciente)."""
    p = tmp_path_factory.mktemp("vid") / "sintetico.mp4"
    w = cv2.VideoWriter(str(p), cv2.VideoWriter_fourcc(*"mp4v"), 30, (320, 240))
    for _ in range(15):
        w.write(np.full((240, 320, 3), 180, np.uint8))
    w.release()
    assert p.stat().st_size > 0
    return p
