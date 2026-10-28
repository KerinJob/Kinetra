# Backlog por etapas

## Etapa 0 — Base técnica (sesión 1)
- [x] T0.1 Inspección del entorno y repositorio. *AC:* versiones registradas en DECISIONS.
- [x] T0.2 Documentación persistente. *AC:* archivos de docs/ creados.
- [x] T0.3 Motor angular puro + pruebas (conocidos, degenerados, no finitos, escala 2D).
- [x] T0.4 Compatibilidad MediaPipe + modelo real cargado en CPU.
- [x] T0.5 CLI video → JSON/CSV con instante, ángulo y calidad.
- [ ] T0.6 Ejecución con video real autorizado. *Bloqueado:* no hay video autorizado.

## Etapa 1 — Persistencia + primer flujo web (HECHO 2026-10-28)
- [x] T1.1 PostgreSQL + SQLAlchemy + Alembic, migración 0001.
- [x] T1.2 FastAPI: login, pacientes, carga privada de video, creación de trabajo.
- [x] T1.3 Worker con SKIP LOCKED y reintento idempotente.
- [x] T1.4 Frontend mínimo + Playwright.
- (antiguo detalle:)
- [ ] ~~T1.1~~ Base PostgreSQL local `kinetra` + SQLAlchemy 2 + Alembic. Modelos: professional, patient,
      appointment, session, evaluation, test_protocol, video_asset, processing_job, measurement_frame.
      *AC:* `alembic upgrade head` en BD vacía; pruebas pytest contra BD de prueba.
- [ ] T1.2 FastAPI: login (JWT/cookie httpOnly, hash argon2/bcrypt), pacientes CRUD básico, carga de video
      privada (validación tamaño/duración/tipo), creación de job. *AC:* pruebas de API con auth y 401/403.
- [ ] T1.3 Worker separado: toma jobs con `SELECT ... FOR UPDATE SKIP LOCKED`, progreso, reintento
      idempotente (borra/reescribe frames del job en transacción). *AC:* prueba de interrupción sin duplicados.
- [ ] T1.4 Frontend React+TS+Vite mínimo en español: login → paciente → subir video → progreso → gráfico/tabla
      de serie con estados de calidad → video con streaming autenticado. *AC:* Playwright del flujo.

## Etapa 2 — Gestión clínica
- [ ] Citas (America/La_Paz) vs sesiones realizadas; evaluaciones; responsable y revisión profesional (F03, F04, F11).
- [ ] Catálogo de pruebas versionado (F05).

## Etapa 3 — Seguimiento
- [ ] Historial y comparación solo entre mediciones compatibles, sin etiquetas de mejoría (F12).
- [ ] Exportación para validación: pares sistema/referencia, tiempos manual/digital (F13).

## Etapa 4 — Operación
- [ ] Instalación reproducible (Docker Compose o script Windows), respaldo/restauración BD + videos (F14).
- [ ] Endurecimiento de seguridad y auditoría.

## Etapa 5 — Validación (requiere decisiones clínicas)
- [ ] Protocolos aprobados, criterios de aceptación previos, pruebas técnicas con videos autorizados, análisis de concordancia.
