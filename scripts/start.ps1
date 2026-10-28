# Inicia Kinetra (API + worker) usando la BD real 'kinetra'. Abrir http://127.0.0.1:8000
# Requiere: scripts/setup_db.ps1 ejecutado, frontend compilado (cd frontend; npm run build).
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
Push-Location (Join-Path $root "backend")
& $py -m alembic upgrade head
$wrk = Start-Process $py -ArgumentList "-m","app.worker" -PassThru -NoNewWindow
try {
  Write-Host "Kinetra en http://127.0.0.1:8000  (Ctrl+C para detener)"
  & $py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} finally {
  Stop-Process -Id $wrk.Id -Force -ErrorAction SilentlyContinue
  Pop-Location
}
