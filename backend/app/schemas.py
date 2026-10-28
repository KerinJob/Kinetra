from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: str
    password: str


class ProfessionalOut(ORM):
    id: int
    email: str
    full_name: str


class PatientIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    document_id: str | None = Field(default=None, max_length=50)
    birth_date: date | None = None
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=5000)


class PatientOut(PatientIn, ORM):
    id: int
    created_at: datetime


class JobOut(ORM):
    id: int
    video_id: UUID
    protocol_code: str
    protocol_version: str
    status: str
    progress: float
    attempts: int
    error: str | None
    summary: dict | None
    config: dict | None
    created_at: datetime
    finished_at: datetime | None


class VideoOut(ORM):
    id: UUID
    patient_id: int
    original_filename: str
    size_bytes: int
    width: int
    height: int
    fps: float
    frame_count: int
    duration_s: float
    created_at: datetime
    jobs: list[JobOut] = []


class FrameOut(ORM):
    frame_index: int
    timestamp_ms: int
    angle_deg: float | None
    quality: str
    min_visibility: float | None
    num_poses: int


class ProtocolOut(BaseModel):
    code: str
    version: str
    name: str
    joint: str
    movement: str
    side: str
    clinical_convention: str
    capture_conditions: str
    validation_status: str
