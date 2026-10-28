"""Almacenamiento privado de videos en disco local (fuera del directorio servido)."""
import hashlib
import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from kinetra_engine.video import probe_video

from ..config import get_settings

ALLOWED_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


class UploadRejected(ValueError):
    pass


def resolve(storage_key: str) -> Path:
    base = get_settings().storage_dir.resolve()
    p = (base / storage_key).resolve()
    if base not in p.parents:
        raise UploadRejected("ruta de almacenamiento inválida")
    return p


async def save_upload(file: UploadFile):
    """Guarda en streaming con límite de tamaño, valida con OpenCV y devuelve (key, sha, size, info)."""
    s = get_settings()
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise UploadRejected(f"extensión no permitida ({ext or 'sin extensión'})")
    key = f"videos/{uuid.uuid4().hex}{ext}"
    dest = resolve(key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    h, size = hashlib.sha256(), 0
    try:
        with open(tmp, "wb") as out:
            while chunk := await file.read(1 << 20):
                size += len(chunk)
                if size > s.max_upload_bytes:
                    raise UploadRejected("el archivo supera el tamaño máximo permitido")
                h.update(chunk)
                out.write(chunk)
        if size == 0:
            raise UploadRejected("archivo vacío")
        os.replace(tmp, dest)
        try:
            info = probe_video(dest)  # valida contenido real, dimensiones, fps y duración
        except (ValueError, FileNotFoundError) as e:
            raise UploadRejected(f"video inválido: {e}")
        if info.frame_count <= 0:
            raise UploadRejected("video sin fotogramas legibles")
        return key, h.hexdigest(), size, info
    except Exception:
        tmp.unlink(missing_ok=True)
        dest.unlink(missing_ok=True)
        raise
