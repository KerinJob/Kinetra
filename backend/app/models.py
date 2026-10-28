"""Modelos de persistencia. Todas las fechas en UTC (timestamptz)."""
import uuid
from datetime import datetime, date, timezone

from sqlalchemy import (String, Text, Boolean, Integer, Float, BigInteger, Date, DateTime,
                        ForeignKey, UniqueConstraint, Index)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class Professional(Base):
    __tablename__ = "professional"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Patient(Base):
    __tablename__ = "patient"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    document_id: Mapped[str | None] = mapped_column(String(50), unique=True)
    birth_date: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("professional.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VideoAsset(Base):
    __tablename__ = "video_asset"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient.id"), index=True)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("professional.id"))
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)  # relativo a storage_dir
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    fps: Mapped[float] = mapped_column(Float)
    frame_count: Mapped[int] = mapped_column(Integer)
    duration_s: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="video", order_by="ProcessingJob.created_at")


JOB_QUEUED, JOB_RUNNING, JOB_DONE, JOB_FAILED = "en_cola", "procesando", "completado", "fallido"


class ProcessingJob(Base):
    __tablename__ = "processing_job"
    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_asset.id"), index=True)
    protocol_code: Mapped[str] = mapped_column(String(50))
    protocol_version: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default=JOB_QUEUED)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    worker_id: Mapped[str | None] = mapped_column(String(100))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config: Mapped[dict | None] = mapped_column(JSONB)
    summary: Mapped[dict | None] = mapped_column(JSONB)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("professional.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    video: Mapped[VideoAsset] = relationship(back_populates="jobs")
    __table_args__ = (Index("ix_job_status", "status"),)


class MeasurementFrame(Base):
    """Serie cruda por fotograma. angle_deg NULL = medición inválida (nunca 0)."""
    __tablename__ = "measurement_frame"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("processing_job.id", ondelete="CASCADE"))
    frame_index: Mapped[int] = mapped_column(Integer)
    timestamp_ms: Mapped[int] = mapped_column(Integer)
    angle_deg: Mapped[float | None] = mapped_column(Float)
    quality: Mapped[str] = mapped_column(String(30))
    min_visibility: Mapped[float | None] = mapped_column(Float)
    num_poses: Mapped[int] = mapped_column(Integer)
    detail: Mapped[str | None] = mapped_column(String(200))
    __table_args__ = (UniqueConstraint("job_id", "frame_index", name="uq_frame_job_index"),)
