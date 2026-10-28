# Prueba E2E (Playwright) contra la BD de PRUEBA kinetra_test. No toca la BD real.
$ErrorActionPreference = "Continue"
function Check($what) { if ($LASTEXITCODE -ne 0) { throw "Falló: $what" } }
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
$testUrl = (Get-Content (Join-Path $root ".env") | Where-Object { $_ -like "KINETRA_TEST_DATABASE_URL=*" }) -replace "^KINETRA_TEST_DATABASE_URL=", ""
if (-not $testUrl) { throw "Falta KINETRA_TEST_DATABASE_URL en .env" }
$env:KINETRA_DATABASE_URL = $testUrl
$env:KINETRA_STORAGE_DIR = Join-Path $root "outputs\e2e_storage"
$env:KINETRA_E2E_PASSWORD = "e2e-" + [guid]::NewGuid().ToString("N")
$port = 8765
$env:KINETRA_E2E_URL = "http://127.0.0.1:$port"

Push-Location (Join-Path $root "backend")
# Se reinicia el esquema de prueba para un estado conocido.
& $py -c "from sqlalchemy import create_engine,text; c=create_engine('$testUrl').connect(); c.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')); c.commit()"
& $py -m alembic upgrade head 2>$null; Check "migración"
& $py -m app.manage create-professional --email e2e@kinetra.local --name "Usuario E2E" --password-env KINETRA_E2E_PASSWORD; Check "usuario"
$api = Start-Process $py -ArgumentList "-m","uvicorn","app.main:app","--port","$port" -PassThru -WindowStyle Hidden
$wrk = Start-Process $py -ArgumentList "-m","app.worker" -PassThru -WindowStyle Hidden
Pop-Location
try {
  Start-Sleep -Seconds 4
  Push-Location (Join-Path $root "frontend")
  npx playwright test
  $code = $LASTEXITCODE
  Pop-Location
} finally {
  Stop-Process -Id $api.Id, $wrk.Id -Force -ErrorAction SilentlyContinue
}
exit $code
