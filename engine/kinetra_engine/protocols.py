"""Protocolos de medición. SOLO contiene una demostración técnica.

Ningún protocolo aquí está aprobado clínicamente. Los umbrales son valores
técnicos provisionales (ver docs/DECISIONS.md), no criterios clínicos.
"""
from dataclasses import dataclass, field

# Índices de MediaPipe Pose (33 landmarks)
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16


@dataclass(frozen=True)
class Protocol:
    code: str
    version: str
    name: str
    joint: str
    movement: str
    side: str
    landmarks: tuple[int, int, int]  # A, B(vértice), C
    angle_space: str  # "2d_pixel"
    clinical_convention: str  # descripción; transformación NO aplicada
    capture_conditions: str
    min_visibility: float  # provisional técnico
    validation_status: str = "DEMO_TECNICA_PENDIENTE_VALIDACION_PROFESIONAL"
    notes: list[str] = field(default_factory=list)


DEMO_ELBOW_FLEXION = {
    side: Protocol(
        code=f"DEMO_FLEX_CODO_{side[0].upper()}",
        version="0.1.0-demo",
        name=f"Flexión de codo ({'izquierdo' if side == 'left' else 'derecho'}) - DEMOSTRACIÓN TÉCNICA",
        joint="codo",
        movement="flexión",
        side=side,
        landmarks=(L_SHOULDER, L_ELBOW, L_WRIST) if side == "left" else (R_SHOULDER, R_ELBOW, R_WRIST),
        angle_space="2d_pixel",
        clinical_convention="PENDIENTE: se reporta solo el ángulo geométrico hombro-codo-muñeca; "
                            "no se aplica conversión clínica.",
        capture_conditions="PENDIENTE: provisionalmente plano sagital, cámara fija, sujeto único.",
        min_visibility=0.5,
    )
    for side in ("left", "right")
}

PROTOCOLS = {p.code: p for p in DEMO_ELBOW_FLEXION.values()}
