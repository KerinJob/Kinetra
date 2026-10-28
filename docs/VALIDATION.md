# Validación y evidencias

Tres niveles separados; ninguno sustituye a otro.

## Nivel 1 — Pruebas automatizadas (datos sintéticos)
| Fecha | Comando | Resultado |
|---|---|---|
| 2026-10-27 | `cd engine; ..\.venv\Scripts\python -m pytest -q` | 25 aprobadas |
| 2026-10-27 | `..\.venv\Scripts\python scripts\check_mediapipe.py` | Modelo real cargado en CPU; 0 poses en imagen en blanco (esperado) |
| 2026-10-27 | CLI sobre `outputs/sintetico_vacio.mp4` (30 fotogramas grises generados con OpenCV, sin personas) | 30/30 `sin_pose`, ángulos vacíos (no 0), CSV + `.meta.json` generados |
| 2026-10-28 | `cd backend; ..\.venv\Scripts\python -m pytest -q` (BD `kinetra_test`) | 8 aprobadas: auth, pacientes, rechazos de carga, flujo completo, reintento sin duplicados |
| 2026-10-28 | `scripts\e2e.ps1` (Playwright, Chromium, BD de prueba) | 2 aprobadas: 401 sin sesión; login→paciente→carga→worker→resultados→logout |

Cubre: ángulos conocidos (0/45/90/120/180, 3D), clamp, degenerados, NaN/Inf, puntos ausentes, dimensiones,
escala 2D con relación de aspecto, estados de calidad, resumen con huecos.

## Nivel 2 — Pruebas técnicas con videos reales autorizados
**Sin ejecutar.** No hay ningún video autorizado disponible. No se ha medido ninguna persona.

## Nivel 3 — Validación con referencias del fisioterapeuta
**Sin ejecutar.** Requiere protocolos aprobados y criterios de aceptación acordados previamente.

## Limitaciones
- La exactitud angular del sistema es desconocida. La confianza/visibilidad del modelo no equivale a exactitud en grados.

## Publicación del código (2026-10-28)
Revisión de archivos incluidos y exclusiones de Git antes del primer commit. Sin cambios funcionales; no se repitieron las pruebas en esta tarea de publicación. Los resultados anteriores conservan su fecha y alcance.
Push intentado: GitHub rechazó la escritura con HTTP 403 para DrKivan. No se confirmó publicación remota.
