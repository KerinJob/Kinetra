# Decisiones técnicas, supuestos y pendientes

## Entorno verificado (2026-10-27)
- Windows 10 build 22631 (64 bits), Python 3.11.4, Node 24.13.0, cliente PostgreSQL 17.5. **Sin Docker.** Sin GPU requerida.
- Carpeta inicial vacía, sin Git → se ejecutó `git init`.

## D-001 MediaPipe Tasks Pose Landmarker (modelo `full`, float16, v1)
- `mediapipe==1.2.0` (pip, rueda para Windows/py3.11) funciona en CPU. Versiones exactas en `engine/requirements.lock.txt`.
- Modelo: `pose_landmarker_full.task`, 9 398 198 bytes, SHA-256
  `5134A3AAD27A58B93DA0088D431F366DA362B44E3CCFBE3462B3827A839011B1`, descargado desde
  `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task`.
  No se versiona en Git (`.gitignore`); el hash se guarda en cada salida.
- Motivo: equilibrio entre precisión y CPU. `lite`/`heavy` quedan como alternativas reversibles.
- Nota: mediapipe instala `opencv-contrib-python` como dependencia; coexiste con `opencv-python-headless`. Revisar al empaquetar.

## D-002 Ángulo 2D en píxeles por defecto
Las coordenadas `z`/world 3D de MediaPipe son estimaciones; no se usan para la demo. Se conserva la posibilidad de 3D en el motor.

## D-003 Calidad por fotograma (orden de evaluación)
`sin_pose` → `sujeto_ambiguo` (>1 persona; `num_poses=2`) → `baja_visibilidad` (min visibilidad de A,B,C < umbral del protocolo)
→ `angulo_invalido` (degenerado/no finito) → `ok`. Umbral demo 0,5 y confianzas MediaPipe 0,5 = **valores técnicos provisionales**, no clínicos.

## D-004 Sin suavizado ni interpolación en v0.1.0
Serie cruda. Se informa el tramo inválido continuo más largo. Mín/máx se rotulan como descriptivos, no ROM.

## D-005 Timestamps
Se usa `CAP_PROP_POS_MSEC`; si no es fiable, `índice/fps`; se fuerza monotonía estricta (requisito de MediaPipe VIDEO).

## D-006 Límites provisionales de archivo
500 MB y 300 s (técnicos, ajustables).

## D-007 Base de datos sin Docker
Se usa PostgreSQL 17 local. Rol propio `kinetra` (no superusuario) creado por `scripts/setup_db.ps1`; el usuario introduce la contraseña de `postgres`, que no se guarda.

## D-008 Backend y sesión
FastAPI 0.162, SQLAlchemy 2.1, Alembic 1.20, psycopg 3. JWT HS256 (8 h) en cookie httpOnly SameSite=Strict; frontend servido desde el mismo origen
(compilado por FastAPI o proxy de Vite). `cookie_secure` debe activarse detrás de HTTPS. Sin roles todavía: todo profesional activo accede a todo.

## D-009 Cola de trabajos en PostgreSQL
Sin Redis/Celery: tabla `processing_job` + `SKIP LOCKED`, heartbeat cada ~1 s, se recupera un trabajo con heartbeat >120 s. Los fotogramas se escriben
en una única transacción (borrar + insertar + estado), lo que evita duplicados. Restricciones en BD: `quality='ok'` ⇒ ángulo no nulo; ángulo en [0,180].

## D-010 Frontend
React 19 + Vite 7 + react-router 7, gráfico SVG propio (sin librería) que corta la línea en los huecos. Fechas mostradas en America/La_Paz.

## Pendientes clínicos
Ver `CLINICAL_PROTOCOLS.md`. Pendientes externos: video real autorizado para prueba técnica; canal de recepción de videos.
