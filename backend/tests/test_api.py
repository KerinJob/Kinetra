from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func


def test_requires_auth(client):
    for path in ["/api/patients", "/api/auth/me", "/api/protocols", "/api/jobs/1",
                 "/api/videos/00000000-0000-0000-0000-000000000000/file"]:
        assert client.get(path).status_code == 401, path


def test_bad_login(client, professional):
    r = client.post("/api/auth/login", json={"email": "prueba@kinetra.local", "password": "mala"})
    assert r.status_code == 401


def test_tampered_cookie(client):
    client.cookies.set("kinetra_session", "x.y.z")
    assert client.get("/api/auth/me").status_code == 401


def test_cookie_flags(client, professional):
    r = client.post("/api/auth/login", json={"email": "prueba@kinetra.local", "password": "clave-de-prueba-123"})
    sc = r.headers["set-cookie"].lower()
    assert "httponly" in sc and "samesite=strict" in sc


def test_patient_crud(auth_client):
    r = auth_client.post("/api/patients", json={"first_name": "Ana", "last_name": "Sintética", "document_id": "T-001"})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert auth_client.get(f"/api/patients/{pid}").json()["first_name"] == "Ana"
    assert any(p["id"] == pid for p in auth_client.get("/api/patients?q=sint").json())
    assert auth_client.post("/api/patients", json={"first_name": "B", "last_name": "C", "document_id": "T-001"}).status_code == 409


def _patient(c):
    return c.post("/api/patients", json={"first_name": "Video", "last_name": "Prueba"}).json()["id"]


def test_upload_rejections(auth_client, tmp_path):
    pid = _patient(auth_client)
    bad = tmp_path / "x.txt"
    bad.write_text("hola")
    r = auth_client.post(f"/api/patients/{pid}/videos", data={"protocol_code": "DEMO_FLEX_CODO_L"},
                         files={"file": ("x.txt", bad.read_bytes())})
    assert r.status_code == 422 and "extensión" in r.json()["detail"]
    r = auth_client.post(f"/api/patients/{pid}/videos", data={"protocol_code": "DEMO_FLEX_CODO_L"},
                         files={"file": ("falso.mp4", b"no es un video" * 100)})
    assert r.status_code == 422 and "inválido" in r.json()["detail"]
    r = auth_client.post(f"/api/patients/{pid}/videos", data={"protocol_code": "NO_EXISTE"},
                         files={"file": ("a.mp4", b"x")})
    assert r.status_code == 422


def test_full_flow_and_idempotent_retry(auth_client, synthetic_video):
    from app.db import SessionLocal
    from app.models import ProcessingJob, MeasurementFrame, JOB_RUNNING
    from app.services.jobs import run_once

    pid = _patient(auth_client)
    r = auth_client.post(f"/api/patients/{pid}/videos", data={"protocol_code": "DEMO_FLEX_CODO_L"},
                         files={"file": ("sintetico.mp4", synthetic_video.read_bytes(), "video/mp4")})
    assert r.status_code == 201, r.text
    video = r.json()
    jid = video["jobs"][0]["id"]
    assert video["jobs"][0]["status"] == "en_cola"

    # Video accesible solo autenticado
    assert auth_client.get(f"/api/videos/{video['id']}/file").status_code == 200

    with SessionLocal() as db:
        assert run_once(db) is True
    job = auth_client.get(f"/api/jobs/{jid}").json()
    assert job["status"] == "completado", job
    assert job["config"]["model_sha256"] and job["config"]["protocol_version"] == "0.1.0-demo"
    frames = auth_client.get(f"/api/jobs/{jid}/frames").json()
    assert len(frames) == 15 and all(f["quality"] == "sin_pose" and f["angle_deg"] is None for f in frames)

    # Simular interrupción: trabajo quedó 'procesando' con heartbeat vencido y frames ya escritos.
    with SessionLocal() as db:
        j = db.get(ProcessingJob, jid)
        j.status, j.heartbeat_at = JOB_RUNNING, datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
        assert run_once(db) is True
        n = db.execute(select(func.count()).select_from(MeasurementFrame).where(MeasurementFrame.job_id == jid)).scalar()
        assert n == 15  # sin duplicados
        assert db.get(ProcessingJob, jid).attempts == 2

    csv = auth_client.get(f"/api/jobs/{jid}/frames.csv")
    assert csv.status_code == 200 and csv.text.count("\n") == 16


def test_logout(auth_client):
    auth_client.post("/api/auth/logout")
    auth_client.cookies.clear()
    assert auth_client.get("/api/auth/me").status_code == 401
