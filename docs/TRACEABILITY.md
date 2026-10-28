# Trazabilidad

| Req. | Implementación | Prueba | Estado |
|---|---|---|---|
| F01 Autenticación / acceso | `backend/app/security.py`, `api.py` | `test_requires_auth`, `test_bad_login`, `test_tampered_cookie`, `test_cookie_flags`, `test_logout`, E2E | Básico listo (sin roles) |
| F02 Pacientes | `api.py`, `App.tsx` | `test_patient_crud`, E2E | Datos básicos listos |
| F05 Catálogo (demo) | `engine/.../protocols.py`, `/api/protocols` | `test_protocols_marked_demo` | Solo demo |
| F06 Carga privada | `services/storage.py`, `/api/videos/{id}/file` | `test_upload_rejections`, `test_full_flow...` | Listo |
| F07 Pose preentrenada | `engine/.../video.py`, `services/jobs.py`, `worker.py` | `check_mediapipe.py`, `test_full_flow...` | Parcial (sin video real) |
| F08 Ángulo + tiempo | `angles.py`, `measurement_frame` | `engine/tests`, `test_full_flow...` | Listo |
| F09 Inválidos | `evaluate_landmarks`, CHECK en BD | `test_quality_*` | Listo |
| F10 Revisión visual | `JobView.tsx` | E2E | Básico |
| F13 Exportación | `/api/jobs/{id}/frames.csv` | `test_full_flow...` | Serie; sin pares de referencia |
| F03, F04, F11, F12, F14 | — | — | Pendiente |
