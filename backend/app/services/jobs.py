"""Cola de trabajos en PostgreSQL. Idempotente: los fotogramas se escriben en una sola
transacción al final, borrando antes cualquier resto del mismo trabajo."""
import os
import socket
import traceback
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete, or_, and_, update, insert
from sqlalchemy.orm import Session

from kinetra_engine.protocols import PROTOCOLS
from kinetra_engine.video import process_video, summarize, frames_as_dicts

from ..config import get_settings
from ..models import ProcessingJob, MeasurementFrame, JOB_QUEUED, JOB_RUNNING, JOB_DONE, JOB_FAILED
from .storage import resolve

WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"


def now():
    return datetime.now(timezone.utc)


def claim_next(db: Session) -> ProcessingJob | None:
    """Toma un trabajo en cola o uno 'procesando' abandonado (heartbeat vencido)."""
    s = get_settings()
    stale = now() - timedelta(seconds=s.job_stale_seconds)
    q = (select(ProcessingJob)
         .where(or_(ProcessingJob.status == JOB_QUEUED,
                    and_(ProcessingJob.status == JOB_RUNNING, ProcessingJob.heartbeat_at < stale)))
         .order_by(ProcessingJob.created_at)
         .with_for_update(skip_locked=True).limit(1))
    job = db.execute(q).scalar_one_or_none()
    if not job:
        db.rollback()
        return None
    if job.attempts >= s.job_max_attempts:
        job.status, job.error, job.finished_at = JOB_FAILED, (job.error or "") + "\nIntentos agotados", now()
        db.commit()
        return None
    job.status, job.attempts, job.worker_id = JOB_RUNNING, job.attempts + 1, WORKER_ID
    job.heartbeat_at = job.started_at = now()
    job.progress, job.error = 0.0, None
    db.commit()
    return job


def run_job(db: Session, job: ProcessingJob) -> None:
    s = get_settings()
    protocol = PROTOCOLS.get(job.protocol_code)
    try:
        if protocol is None or protocol.version != job.protocol_version:
            raise ValueError("protocolo desconocido o versión distinta a la solicitada")
        last = [now()]

        def progress(i, total):
            if (now() - last[0]).total_seconds() >= 1.0:
                last[0] = now()
                db.execute(update(ProcessingJob).where(ProcessingJob.id == job.id)
                           .values(progress=(i / total) if total else 0.0, heartbeat_at=last[0]))
                db.commit()

        _, frames, config = process_video(resolve(job.video.storage_key), protocol, s.model_path, progress)
        rows = [{**f, "job_id": job.id} for f in frames_as_dicts(frames)]
        # Transacción única: limpieza + inserción + estado final.
        db.execute(delete(MeasurementFrame).where(MeasurementFrame.job_id == job.id))
        if rows:
            db.execute(insert(MeasurementFrame), rows)
        job.config, job.summary = config, summarize(frames)
        job.status, job.progress, job.finished_at = JOB_DONE, 1.0, now()
        db.commit()
    except Exception as e:
        db.rollback()
        job = db.get(ProcessingJob, job.id)
        job.error = f"{type(e).__name__}: {e}"
        job.status = JOB_QUEUED if job.attempts < s.job_max_attempts else JOB_FAILED
        if job.status == JOB_FAILED:
            job.finished_at = now()
        db.commit()
        traceback.print_exc()


def run_once(db: Session) -> bool:
    job = claim_next(db)
    if job is None:
        return False
    run_job(db, job)
    return True
