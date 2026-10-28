# STATUS — actualizado 2026-10-28

## Hecho
- **Etapa 0:** motor angular + calidad por fotograma + CLI video→JSON/CSV; MediaPipe 1.2.0 en CPU.
- **Etapa 1 (primer flujo web completo):**
  - PostgreSQL 17 local: rol `kinetra`, BD `kinetra` (uso) y `kinetra_test` (pruebas; se borra en cada ejecución). Creados por el autor con `scripts/setup_db.ps1`. Credenciales en `.env` (no versionado; no mostrar su contenido).
  - `backend/`: FastAPI + SQLAlchemy 2 + Alembic (migración `0001`). Auth argon2 + JWT en cookie httpOnly SameSite=Strict.
    Pacientes, carga privada validada, streaming autenticado, trabajos, mediciones y CSV.
  - Worker separado (`python -m app.worker`): SKIP LOCKED, heartbeat, máx. 3 intentos, escritura transaccional sin duplicados.
  - `frontend/`: React 19 + TS + Vite, en español. Se compila a `frontend/dist`, que FastAPI sirve en :8000.
  - Pruebas: motor 25, backend 8, Playwright 2. Todas aprobadas el 2026-10-28.
- Scripts: `scripts/setup_db.ps1` (ya ejecutado), `scripts/start.ps1` (uso diario), `scripts/e2e.ps1`.
- Git: autor autorizó el primer commit y la publicación del código actual en https://github.com/KerinJob/Kinetra.git (rama main), el 2026-10-28. Videos, datos privados, modelo y credenciales excluidos.

## Bloqueado / pendiente externo
- Sin video real autorizado: el Nivel 2 de validación no se ha ejecutado. Nunca fabricarlo.
- Decisiones clínicas: ver `CLINICAL_PROTOCOLS.md`.
- Docker no disponible (Compose podría escribirse, pero no verificarse aquí).

## Deuda técnica conocida
- Sin roles ni autorización por paciente (todo profesional activo ve todo). No hay registro de auditoría.
- No hay protección CSRF explícita (se confía en SameSite=Strict y el mismo origen).
- No hay límite de recursos del worker (CPU/tiempo por trabajo) ni limpieza de videos huérfanos.
- `mediapipe` instala `opencv-contrib-python` junto con `opencv-python-headless` (duplicado; revisar al empaquetar).
- Aviso de Starlette: TestClient con httpx está obsoleto (no afecta).

## Lecciones del entorno (evitar repetir fallos)
- PowerShell 5: con `$ErrorActionPreference="Stop"`, la salida de Alembic a stderr aborta el script. Usar `Continue` y comprobar `$LASTEXITCODE`.
- `alembic init` no acepta `-q`; los archivos de Alembic ya están escritos a mano.
- Las pruebas de Playwright corren como ESM: no usar `__dirname`.
- `cv2.VideoWriter` falla en silencio si la carpeta destino no existe.
- `psql -U postgres` requiere una contraseña que el agente no tiene: usar siempre el rol `kinetra` desde `.env`.

## Siguiente tarea exacta (Etapa 2, cuando el autor lo indique)
Ver `docs/NEXT_TASK.md` (instrucciones listas para delegar).


## Publicación pendiente
Primer commit local creado en main; origin apunta a https://github.com/KerinJob/Kinetra.git. Push rechazado con HTTP 403: Git autentica como DrKivan, sin permiso de escritura sobre KerinJob/Kinetra. Hace falta iniciar sesión con una cuenta autorizada o conceder acceso a DrKivan. Después ejecutar: git push -u origin main.
