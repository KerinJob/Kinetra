"""Esquema inicial: profesionales, pacientes, videos, trabajos y mediciones

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TS = sa.DateTime(timezone=True)


def upgrade():
    op.create_table(
        "professional",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_table(
        "patient",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("document_id", sa.String(50), unique=True),
        sa.Column("birth_date", sa.Date),
        sa.Column("phone", sa.String(50)),
        sa.Column("notes", sa.Text),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("professional.id"), nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_table(
        "video_asset",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", sa.Integer, sa.ForeignKey("patient.id"), nullable=False, index=True),
        sa.Column("uploaded_by_id", sa.Integer, sa.ForeignKey("professional.id"), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False, unique=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("width", sa.Integer, nullable=False),
        sa.Column("height", sa.Integer, nullable=False),
        sa.Column("fps", sa.Float, nullable=False),
        sa.Column("frame_count", sa.Integer, nullable=False),
        sa.Column("duration_s", sa.Float, nullable=False),
        sa.Column("created_at", TS, nullable=False),
    )
    op.create_table(
        "processing_job",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_id", pg.UUID(as_uuid=True), sa.ForeignKey("video_asset.id"), nullable=False, index=True),
        sa.Column("protocol_code", sa.String(50), nullable=False),
        sa.Column("protocol_version", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress", sa.Float, nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("error", sa.Text),
        sa.Column("worker_id", sa.String(100)),
        sa.Column("heartbeat_at", TS),
        sa.Column("config", pg.JSONB),
        sa.Column("summary", pg.JSONB),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("professional.id"), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("started_at", TS),
        sa.Column("finished_at", TS),
    )
    op.create_index("ix_job_status", "processing_job", ["status"])
    op.create_table(
        "measurement_frame",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("processing_job.id", ondelete="CASCADE"), nullable=False),
        sa.Column("frame_index", sa.Integer, nullable=False),
        sa.Column("timestamp_ms", sa.Integer, nullable=False),
        sa.Column("angle_deg", sa.Float),
        sa.Column("quality", sa.String(30), nullable=False),
        sa.Column("min_visibility", sa.Float),
        sa.Column("num_poses", sa.Integer, nullable=False),
        sa.Column("detail", sa.String(200)),
        sa.UniqueConstraint("job_id", "frame_index", name="uq_frame_job_index"),
        sa.CheckConstraint("angle_deg IS NULL OR (angle_deg >= 0 AND angle_deg <= 180)", name="ck_angle_range"),
        sa.CheckConstraint("quality <> 'ok' OR angle_deg IS NOT NULL", name="ck_ok_has_angle"),
    )


def downgrade():
    for t in ["measurement_frame", "processing_job", "video_asset", "patient", "professional"]:
        op.drop_table(t)
