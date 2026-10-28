# Siguiente tarea — Etapa 2: gestión clínica (F03, F04, F05, F11)

Instrucción para el agente que retome: lee `AGENTS.md` y `docs/STATUS.md`, y luego ejecuta esto. No pidas al autor la especificación original.

## Objetivo
Diferenciar citas de sesiones realizadas, registrar evaluaciones con responsable y revisión profesional,
y hacer persistente y versionado el catálogo de pruebas. Todo en español, presentado en America/La_Paz y almacenado en UTC.

## Alcance
1. **Migración `0002`** (no editar la `0001`):
   - `appointment`: paciente, profesional, `scheduled_start`/`scheduled_end` (timestamptz), estado (`programada`, `realizada`, `cancelada`, `no_asistio`), notas, creado_por.
   - `clinical_session`: paciente, profesional responsable, `performed_at`, `appointment_id` nulo (una sesión puede existir sin cita), modalidad (`presencial`, `control_por_video`), notas.
   - `evaluation`: sesión, protocolo (código y versión), lado, evaluador responsable, creada_en; estado de revisión (`pendiente`, `revisada`), `reviewed_by`, `reviewed_at`, comentario profesional.
   - `test_protocol` en BD: código, versión, articulación, movimiento, lado, landmarks, espacio angular, convención clínica, condiciones de captura, `validation_status`. Clave única (código, versión). Sembrar solo los dos protocolos DEMO actuales.
   - Vincular `processing_job` (o `video_asset`) a `evaluation` con FK nula, para no romper los datos existentes.
2. **API + servicios**: CRUD de citas (con validación fin > inicio y sin solapamiento para el mismo profesional), registrar una sesión desde una cita (la marca como `realizada`) o sin cita, crear evaluaciones, subir video dentro de una evaluación y marcar una revisión (registra quién y cuándo).
   La revisión no genera interpretación automática.
3. **Frontend**: agenda simple por día o semana (America/La_Paz), ficha del paciente con sesiones y evaluaciones, botón «Marcar como revisada» con comentario.
4. **Pruebas**: pytest para zonas horarias (una cita 08:00 en La Paz se guarda como 12:00 UTC), solapamiento, cita→sesión, revisión con responsable y 401 en todas las rutas nuevas. Ampliar el E2E con el flujo cita → sesión → evaluación → video → revisión.

## Fuera de alcance (no hacer)
Recordatorios por WhatsApp, pagos, portal del paciente, protocolos clínicos nuevos o umbrales clínicos, comparación entre sesiones (Etapa 3).

## Criterios de aceptación
- `alembic upgrade head` funciona sobre la BD `kinetra` existente sin perder datos.
- Las tres suites pasan (motor, backend, E2E).
- `STATUS.md`, `TRACEABILITY.md`, `VALIDATION.md`, `DECISIONS.md` y `BACKLOG.md` actualizados.

## Posible delegación (máximo 2 ejecutores)
- Ejecutor A: `backend/` (migración, modelos, servicios, API, pytest).
- Ejecutor B: `frontend/` (pantallas y E2E), sobre el contrato de API definido primero por el agente principal en `docs/API_ETAPA2.md`.
- El agente principal integra, ejecuta las tres suites y actualiza la documentación.

## Pendientes posteriores (para próximas instrucciones del autor)
- Etapa 3: historial y comparación entre mediciones compatibles; exportación de pares sistema/referencia y tiempos manual vs digital.
- Etapa 4: roles y permisos, auditoría, CSRF, respaldo y restauración (`pg_dump` + `storage/`), instalación reproducible (Docker Compose o instalador Windows).
- Etapa 5: validación (requiere decisiones clínicas del autor y de los profesionales).
