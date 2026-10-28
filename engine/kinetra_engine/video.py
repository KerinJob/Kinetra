"""Procesamiento de video con MediaPipe Tasks Pose Landmarker (modo VIDEO, CPU).

Produce una serie temporal cruda por fotograma: instante, ángulo geométrico,
estado de calidad. No suaviza, no interpola, no calcula ROM.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Iterator, Optional

import cv2

from . import ENGINE_VERSION
from .angles import angle_at_vertex, to_pixel_space
from .protocols import Protocol

# Estados de calidad por fotograma
OK = "ok"
NO_POSE = "sin_pose"
MULTI_POSE = "sujeto_ambiguo"
LOW_VIS = "baja_visibilidad"
INVALID = "angulo_invalido"

MAX_FILE_BYTES = 500 * 1024 * 1024  # límite técnico provisional
MAX_DURATION_S = 300


@dataclass
class FrameMeasurement:
    frame_index: int
    timestamp_ms: int
    angle_deg: Optional[float]
    quality: str
    min_visibility: Optional[float]
    num_poses: int
    detail: str = ""


@dataclass
class VideoInfo:
    path: str
    sha256: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration_s: float


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_video(path: Path) -> VideoInfo:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("archivo supera el tamaño máximo permitido")
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError("no se pudo abrir el video (formato no soportado o archivo corrupto)")
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    if w <= 0 or h <= 0:
        raise ValueError("dimensiones de video inválidas")
    if fps <= 0 or not math.isfinite(fps):
        raise ValueError("fps inválido")
    dur = n / fps if n > 0 else 0.0
    if dur > MAX_DURATION_S:
        raise ValueError("video supera la duración máxima permitida")
    return VideoInfo(str(path), sha256_file(path), w, h, fps, n, dur)


def evaluate_landmarks(poses, protocol: Protocol, width: int, height: int):
    """Lógica de calidad separada de MediaPipe para poder probarla con datos sintéticos.

    `poses` es una lista de listas de landmarks con atributos x, y, visibility.
    Devuelve (angle_deg|None, quality, min_visibility|None, detail).
    """
    if not poses:
        return None, NO_POSE, None, ""
    if len(poses) > 1:
        return None, MULTI_POSE, None, f"{len(poses)} personas detectadas"
    lms = poses[0]
    pts = [lms[i] for i in protocol.landmarks]
    vis = min(float(getattr(p, "visibility", 0.0) or 0.0) for p in pts)
    if vis < protocol.min_visibility:
        return None, LOW_VIS, vis, ""
    px = [to_pixel_space((p.x, p.y), width, height) for p in pts]
    r = angle_at_vertex(*px)
    if not r.valid:
        return None, INVALID, vis, r.reason
    return r.value_deg, OK, vis, ""


def process_video(
    path: Path,
    protocol: Protocol,
    model_path: Path,
    progress: Optional[Callable[[int, int], None]] = None,
) -> tuple[VideoInfo, list[FrameMeasurement], dict]:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    info = probe_video(path)
    options = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(model_path),
                                           delegate=mp_python.BaseOptions.Delegate.CPU),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=2,  # 2 para detectar sujeto ambiguo
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    config = {
        "engine_version": ENGINE_VERSION,
        "mediapipe_version": mp.__version__,
        "model_file": model_path.name,
        "model_sha256": sha256_file(model_path),
        "num_poses": 2,
        "min_pose_detection_confidence": 0.5,
        "min_pose_presence_confidence": 0.5,
        "min_tracking_confidence": 0.5,
        "angle_space": protocol.angle_space,
        "smoothing": None,
        "interpolation": None,
        "protocol_code": protocol.code,
        "protocol_version": protocol.version,
        "protocol_validation_status": protocol.validation_status,
    }
    out: list[FrameMeasurement] = []
    cap = cv2.VideoCapture(str(path))
    last_ts = -1
    idx = 0
    with vision.PoseLandmarker.create_from_options(options) as lm:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            pos = cap.get(cv2.CAP_PROP_POS_MSEC)
            ts = int(round(pos)) if pos and pos > 0 else int(round(idx * 1000.0 / info.fps))
            if ts <= last_ts:  # MediaPipe exige timestamps estrictamente crecientes
                ts = last_ts + 1
            last_ts = ts
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
            ang, q, vis, det = evaluate_landmarks(res.pose_landmarks, protocol, info.width, info.height)
            out.append(FrameMeasurement(idx, ts, ang, q, vis, len(res.pose_landmarks), det))
            idx += 1
            if progress:
                progress(idx, info.frame_count)
    cap.release()
    return info, out, config


def summarize(frames: list[FrameMeasurement]) -> dict:
    """Resumen descriptivo. NO es ROM clínico."""
    total = len(frames)
    counts: dict[str, int] = {}
    for f in frames:
        counts[f.quality] = counts.get(f.quality, 0) + 1
    valid = [f.angle_deg for f in frames if f.quality == OK]
    # Mayor tramo continuo sin medición válida
    longest, cur = 0, 0
    for f in frames:
        cur = 0 if f.quality == OK else cur + 1
        longest = max(longest, cur)
    return {
        "frames_total": total,
        "frames_by_quality": counts,
        "valid_ratio": (len(valid) / total) if total else 0.0,
        "longest_invalid_run_frames": longest,
        "geometric_angle_min_deg": min(valid) if valid else None,
        "geometric_angle_max_deg": max(valid) if valid else None,
        "note": "Estadísticos descriptivos del ángulo geométrico; no constituyen ROM clínico validado.",
    }


def frames_as_dicts(frames):
    return [asdict(f) for f in frames]
