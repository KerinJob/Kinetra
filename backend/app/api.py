"""Rutas HTTP. Solo validan, autorizan y delegan; el procesamiento ocurre en el worker."""
import csv
import io
from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from kinetra_engine.protocols import PROTOCOLS

from .config import get_settings
from .db import get_db
from .models import Patient, Professional, VideoAsset, ProcessingJob, MeasurementFrame, JOB_QUEUED
from .schemas import (LoginIn, ProfessionalOut, PatientIn, PatientOut, VideoOut, JobOut, FrameOut, ProtocolOut)
from .security import COOKIE_NAME, create_token, current_professional, verify_password
from .services.storage import save_upload, resolve, UploadRejected

router = APIRouter(prefix="/api")
auth = Depends(current_professional)


# --- Autenticación ---
@router.post("/auth/login", response_model=ProfessionalOut)
def login(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    prof = db.execute(select(Professional).where(Professional.email == data.email.lower().strip())).scalar_one_or_none()
    if not prof or not prof.is_active or not verify_password(data.password, prof.password_hash):
        raise HTTPException(401, "Credenciales inválidas")
    s = get_settings()
    response.set_cookie(COOKIE_NAME, create_token(prof.id), httponly=True, samesite="strict",
                        secure=s.cookie_secure, max_age=s.session_hours * 3600, path="/")
    return prof


@router.post("/auth/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/auth/me", response_model=ProfessionalOut)
def me(prof: Professional = auth):
    return prof


# --- Protocolos ---
@router.get("/protocols", response_model=list[ProtocolOut], dependencies=[auth])
def protocols():
    return [ProtocolOut(**{k: v for k, v in asdict(p).items() if k in ProtocolOut.model_fields})
            for p in PROTOCOLS.values()]


# --- Pacientes ---
@router.get("/patients", response_model=list[PatientOut], dependencies=[auth])
def list_patients(q: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Patient).order_by(Patient.last_name, Patient.first_name)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Patient.first_name.ilike(like), Patient.last_name.ilike(like),
                              Patient.document_id.ilike(like)))
    return db.execute(stmt.limit(200)).scalars().all()


@router.post("/patients", response_model=PatientOut, status_code=201)
def create_patient(data: PatientIn, db: Session = Depends(get_db), prof: Professional = auth):
    p = Patient(**data.model_dump(), created_by_id=prof.id)
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya existe un paciente con ese documento")
    return p


@router.get("/patients/{pid}", response_model=PatientOut, dependencies=[auth])
def get_patient(pid: int, db: Session = Depends(get_db)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Paciente no encontrado")
    return p


# --- Videos ---
@router.get("/patients/{pid}/videos", response_model=list[VideoOut], dependencies=[auth])
def list_videos(pid: int, db: Session = Depends(get_db)):
    return db.execute(select(VideoAsset).where(VideoAsset.patient_id == pid)
                      .options(selectinload(VideoAsset.jobs)).order_by(VideoAsset.created_at.desc())).scalars().all()


@router.post("/patients/{pid}/videos", response_model=VideoOut, status_code=201)
async def upload_video(pid: int, file: UploadFile = File(...), protocol_code: str = Form(...),
                       db: Session = Depends(get_db), prof: Professional = auth):
    if not db.get(Patient, pid):
        raise HTTPException(404, "Paciente no encontrado")
    proto = PROTOCOLS.get(protocol_code)
    if not proto:
        raise HTTPException(422, "Protocolo desconocido")
    try:
        key, sha, size, info = await save_upload(file)
    except UploadRejected as e:
        raise HTTPException(422, str(e))
    v = VideoAsset(patient_id=pid, uploaded_by_id=prof.id, original_filename=(file.filename or "")[:255],
                   storage_key=key, sha256=sha, size_bytes=size, width=info.width, height=info.height,
                   fps=info.fps, frame_count=info.frame_count, duration_s=info.duration_s)
    db.add(v)
    db.flush()
    db.add(ProcessingJob(video_id=v.id, protocol_code=proto.code, protocol_version=proto.version,
                         status=JOB_QUEUED, created_by_id=prof.id))
    db.commit()
    db.refresh(v)
    return v


@router.get("/videos/{vid}/file", dependencies=[auth])
def video_file(vid: UUID, db: Session = Depends(get_db)):
    v = db.get(VideoAsset, vid)
    if not v:
        raise HTTPException(404, "Video no encontrado")
    path = resolve(v.storage_key)
    if not path.is_file():
        raise HTTPException(410, "Archivo no disponible en almacenamiento")
    return FileResponse(path, headers={"Cache-Control": "private, no-store"})


# --- Trabajos y mediciones ---
def _job(db, jid) -> ProcessingJob:
    j = db.get(ProcessingJob, jid)
    if not j:
        raise HTTPException(404, "Trabajo no encontrado")
    return j


@router.get("/jobs/{jid}", response_model=JobOut, dependencies=[auth])
def get_job(jid: int, db: Session = Depends(get_db)):
    return _job(db, jid)


@router.get("/jobs/{jid}/frames", response_model=list[FrameOut], dependencies=[auth])
def get_frames(jid: int, db: Session = Depends(get_db)):
    _job(db, jid)
    return db.execute(select(MeasurementFrame).where(MeasurementFrame.job_id == jid)
                      .order_by(MeasurementFrame.frame_index)).scalars().all()


@router.get("/jobs/{jid}/frames.csv", dependencies=[auth])
def export_frames(jid: int, db: Session = Depends(get_db)):
    j = _job(db, jid)
    rows = db.execute(select(MeasurementFrame).where(MeasurementFrame.job_id == jid)
                      .order_by(MeasurementFrame.frame_index)).scalars().all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["job_id", "protocol_code", "protocol_version", "frame_index", "timestamp_ms",
                "angle_deg", "quality", "min_visibility", "num_poses"])
    for r in rows:
        w.writerow([j.id, j.protocol_code, j.protocol_version, r.frame_index, r.timestamp_ms,
                    "" if r.angle_deg is None else f"{r.angle_deg:.3f}", r.quality,
                    "" if r.min_visibility is None else f"{r.min_visibility:.3f}", r.num_poses])
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="trabajo_{j.id}.csv"'})
