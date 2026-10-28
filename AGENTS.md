# AGENTS.md — Kinetra

Instrucciones para retomar el trabajo:

1. Leer `docs/STATUS.md` (estado real y siguiente tarea exacta). Consultar otros docs solo si hace falta.
2. Fuente de requisitos: `docs/PROJECT_SPEC.md` (incluye §8 forma de trabajo; no pedir el documento académico). Decisiones: `docs/DECISIONS.md`.
3. Entorno: Windows, PowerShell 5, Python 3.11 en `.venv` (`.\.venv\Scripts\python`), Node 24, PostgreSQL 17 local (servicio `postgresql-x64-17`). Sin Docker en esta máquina.
4. Pruebas del motor: `cd engine; ..\.venv\Scripts\python -m pytest -q`.
   Backend (BD `kinetra_test`, ver `.env`): `cd backend; ..\.venv\Scripts\python -m pytest -q`. E2E: `scripts\e2e.ps1`.
   Todas deben seguir pasando antes de cerrar una tarea.
5. Reglas no negociables: no diagnóstico ni prescripción; no inventar protocolos/umbrales clínicos;
   medición inválida ≠ 0; no ROM = max−min; no simular ejecuciones; no subir videos, datos clínicos
   ni credenciales a Git (ver `.gitignore`); no clasificar diferencias como mejoría/deterioro.
6. Actualizar `docs/STATUS.md` al terminar cada tarea; `docs/TRACEABILITY.md` y `docs/VALIDATION.md` con evidencias.
7. Interfaz en español; zona horaria de presentación America/La_Paz; almacenamiento en UTC.
8. Capas: `engine/` (procesamiento puro) · `backend/app/{api,schemas}` (presentación HTTP) · `backend/app/services` (lógica) ·
   `backend/app/{models,db}` + `migrations/` (persistencia) · `backend/app/worker.py` (proceso de video) · `frontend/`.
   Todo cambio de esquema se hace con una nueva migración Alembic; no editar `0001`.
9. Delegación: máximo 2 ejecutores con archivos separados; el agente principal integra y prueba.
