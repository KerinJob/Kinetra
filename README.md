# Kinetra

Sistema web de medición angular por video para el Centro Kinesport Tarija (proyecto de grado).
El único protocolo incluido es una **demostración técnica pendiente de validación profesional**.
El sistema no diagnostica ni prescribe, y su exactitud angular aún no está establecida.

## Requisitos (Windows)
Python 3.11, Node 20+ y PostgreSQL 17 (servicio activo).

## Instalación (una sola vez)
```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.lock.txt
.\.venv\Scripts\pip install -e engine
Invoke-WebRequest https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task -OutFile engine\models\pose_landmarker_full.task
powershell -ExecutionPolicy Bypass -File scripts\setup_db.ps1      # pide la contraseña de 'postgres'; crea .env
cd backend; ..\.venv\Scripts\python -m alembic upgrade head; cd ..
cd backend; ..\.venv\Scripts\python -m app.manage create-professional --email tu@correo --name "Tu Nombre"; cd ..
cd frontend; npm install; npm run build; cd ..
```

## Uso diario
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```
Luego abre http://127.0.0.1:8000. El script levanta la API y el worker de video; se detienen con Ctrl+C.

## Pruebas
```powershell
cd engine;  ..\.venv\Scripts\python -m pytest -q; cd ..     # motor (sintético)
cd backend; ..\.venv\Scripts\python -m pytest -q; cd ..     # API + worker (BD kinetra_test)
powershell -ExecutionPolicy Bypass -File scripts\e2e.ps1     # Playwright (BD kinetra_test)
```

## Motor por línea de comandos (sin web)
```powershell
cd engine
..\.venv\Scripts\python -m kinetra_engine.cli RUTA\video.mp4 --protocol DEMO_FLEX_CODO_L --out ..\outputs\resultado.json
```

## Estructura
- `engine/`: procesamiento (MediaPipe, cálculo angular, calidad). No depende de la web.
- `backend/`: API FastAPI, persistencia (SQLAlchemy/Alembic), servicios y worker.
- `frontend/`: interfaz React en español.
- `storage/`: videos privados (fuera de Git). `.env`: credenciales (fuera de Git).
