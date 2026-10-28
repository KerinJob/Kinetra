from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_prefix="KINETRA_", extra="ignore")

    database_url: str = ""
    test_database_url: str = ""
    secret_key: str = ""
    storage_dir: Path = ROOT / "storage"
    model_path: Path = ROOT / "engine" / "models" / "pose_landmarker_full.task"
    session_hours: int = 8
    cookie_secure: bool = False  # True detrás de HTTPS
    max_upload_bytes: int = 500 * 1024 * 1024
    job_max_attempts: int = 3
    job_stale_seconds: int = 120
    display_timezone: str = "America/La_Paz"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.database_url or not s.secret_key:
        raise RuntimeError("Falta configuración: ejecute scripts/setup_db.ps1 para crear .env")
    return s
