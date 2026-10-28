"""Cálculo angular geométrico independiente de MediaPipe.

Devuelve el ángulo GEOMÉTRICO en el vértice B (0-180°). La convención clínica
se aplica aparte (ver protocols.py); nunca se aplica 180-ángulo automáticamente.
Una medición inválida se representa con un resultado inválido, nunca con 0.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

DEGENERATE_EPS = 1e-6


@dataclass(frozen=True)
class AngleResult:
    value_deg: Optional[float]
    valid: bool
    reason: str = "ok"


class AngleError(ValueError):
    pass


def _as_point(p: Sequence[float] | None, name: str) -> np.ndarray:
    if p is None:
        raise AngleError(f"punto {name} ausente")
    arr = np.asarray(p, dtype=float)
    if arr.ndim != 1 or arr.size not in (2, 3):
        raise AngleError(f"punto {name} debe tener 2 o 3 coordenadas")
    if not np.all(np.isfinite(arr)):
        raise AngleError(f"punto {name} contiene valores no finitos")
    return arr


def angle_at_vertex(a, b, c) -> AngleResult:
    """Ángulo ABC en grados con vértice en B."""
    try:
        A, B, C = _as_point(a, "A"), _as_point(b, "B"), _as_point(c, "C")
    except AngleError as e:
        return AngleResult(None, False, str(e))
    if not (A.size == B.size == C.size):
        return AngleResult(None, False, "dimensiones inconsistentes")
    u, v = A - B, C - B
    nu, nv = float(np.linalg.norm(u)), float(np.linalg.norm(v))
    if nu < DEGENERATE_EPS or nv < DEGENERATE_EPS:
        return AngleResult(None, False, "vector degenerado")
    cosang = float(np.dot(u, v)) / (nu * nv)
    cosang = max(-1.0, min(1.0, cosang))
    deg = math.degrees(math.acos(cosang))
    if not math.isfinite(deg):
        return AngleResult(None, False, "resultado no finito")
    return AngleResult(deg, True)


def to_pixel_space(norm_xy: Sequence[float], width: int, height: int) -> tuple[float, float]:
    """Convierte coordenadas normalizadas [0,1] a píxeles conservando la relación de aspecto."""
    if width <= 0 or height <= 0:
        raise AngleError("dimensiones de imagen inválidas")
    return float(norm_xy[0]) * width, float(norm_xy[1]) * height
