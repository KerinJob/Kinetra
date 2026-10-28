"""Pruebas automatizadas con datos SINTÉTICOS (no son validación clínica)."""
import math
from types import SimpleNamespace as P

import pytest

from kinetra_engine.angles import angle_at_vertex, to_pixel_space, AngleError
from kinetra_engine.protocols import PROTOCOLS
from kinetra_engine import video as V


@pytest.mark.parametrize("a,b,c,exp", [
    ((1, 0), (0, 0), (0, 1), 90.0),
    ((1, 0), (0, 0), (-1, 0), 180.0),
    ((1, 0), (0, 0), (2, 0), 0.0),
    ((1, 0), (0, 0), (1, 1), 45.0),
    ((1, 0), (0, 0), (math.cos(math.radians(120)), math.sin(math.radians(120))), 120.0),
    ((1, 0, 0), (0, 0, 0), (0, 0, 1), 90.0),
])
def test_known_angles(a, b, c, exp):
    r = angle_at_vertex(a, b, c)
    assert r.valid and r.value_deg == pytest.approx(exp, abs=1e-9)


def test_clamp_near_collinear():
    r = angle_at_vertex((1e6, 1e-10), (0, 0), (2e6, 0))
    assert r.valid and 0 <= r.value_deg < 1e-6


@pytest.mark.parametrize("a,b,c", [
    ((0, 0), (0, 0), (1, 1)),
    ((1, 1), (0, 0), (0, 0)),
    ((5, 5), (5, 5), (5, 5)),
])
def test_degenerate_rejected_not_zero(a, b, c):
    r = angle_at_vertex(a, b, c)
    assert not r.valid and r.value_deg is None and "degenerado" in r.reason


@pytest.mark.parametrize("a", [None, (float("nan"), 0), (float("inf"), 0), (1,), (1, 2, 3, 4)])
def test_invalid_points(a):
    r = angle_at_vertex(a, (0, 0), (1, 0))
    assert not r.valid and r.value_deg is None


def test_mixed_dimensions():
    assert not angle_at_vertex((1, 0), (0, 0, 0), (0, 1)).valid


def test_2d_scale_preserves_aspect():
    # En normalizado parece 45°, pero en un frame 1920x1080 no lo es.
    a, b, c = (0.6, 0.5), (0.5, 0.5), (0.5, 0.4)
    w, h = 1920, 1080
    assert angle_at_vertex(a, b, c).value_deg == pytest.approx(90)
    a2, b2, c2 = (0.6, 0.5), (0.5, 0.5), (0.6, 0.4)
    naive = angle_at_vertex(a2, b2, c2).value_deg
    px = angle_at_vertex(*(to_pixel_space(p, w, h) for p in (a2, b2, c2))).value_deg
    assert naive == pytest.approx(45)
    assert px == pytest.approx(math.degrees(math.atan2(108, 192)), abs=1e-9)
    assert px != pytest.approx(naive, abs=1)


def test_pixel_space_rejects_bad_dims():
    with pytest.raises(AngleError):
        to_pixel_space((0.5, 0.5), 0, 100)


def _pose(vis=0.9, elbow=(0.5, 0.5)):
    lms = [P(x=0.0, y=0.0, visibility=0.0) for _ in range(33)]
    lms[11] = P(x=0.5, y=0.3, visibility=vis)
    lms[13] = P(x=elbow[0], y=elbow[1], visibility=vis)
    lms[15] = P(x=0.7, y=0.5, visibility=vis)
    return lms


PROTO = PROTOCOLS["DEMO_FLEX_CODO_L"]


def test_quality_no_pose():
    assert V.evaluate_landmarks([], PROTO, 100, 100)[:2] == (None, V.NO_POSE)


def test_quality_multi_pose():
    assert V.evaluate_landmarks([_pose(), _pose()], PROTO, 100, 100)[:2] == (None, V.MULTI_POSE)


def test_quality_low_visibility():
    assert V.evaluate_landmarks([_pose(vis=0.1)], PROTO, 100, 100)[:2] == (None, V.LOW_VIS)


def test_quality_ok_square_frame():
    ang, q, *_ = V.evaluate_landmarks([_pose()], PROTO, 100, 100)
    assert q == V.OK and ang == pytest.approx(90)


def test_quality_degenerate():
    ang, q, _, det = V.evaluate_landmarks([_pose(elbow=(0.5, 0.3))], PROTO, 100, 100)
    assert q == V.INVALID and ang is None


def test_summary_not_rom_and_gaps():
    F = V.FrameMeasurement
    fr = [F(0, 0, 10.0, V.OK, .9, 1), F(1, 33, None, V.NO_POSE, None, 0),
          F(2, 66, None, V.NO_POSE, None, 0), F(3, 99, 50.0, V.OK, .9, 1)]
    s = V.summarize(fr)
    assert s["longest_invalid_run_frames"] == 2
    assert s["valid_ratio"] == 0.5
    assert "no constituyen ROM" in s["note"]


def test_protocols_marked_demo():
    for p in PROTOCOLS.values():
        assert p.validation_status.startswith("DEMO_TECNICA")
