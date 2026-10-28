# Configura PostgreSQL local para Kinetra (ejecutar UNA vez).
# Pide la contraseña del superusuario 'postgres' (no se guarda), crea el rol 'kinetra'
# con contraseña aleatoria y las bases 'kinetra' y 'kinetra_test'. Escribe .env (ignorado por Git).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"
if (Test-Path $envFile) { Write-Host ".env ya existe; no se modifica." ; exit 0 }

$sec = Read-Host "Contraseña del usuario 'postgres' de PostgreSQL" -AsSecureString
$env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
$pw = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
$secret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })

$sql = @"
DO `$`$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='kinetra') THEN
    CREATE ROLE kinetra LOGIN PASSWORD '$pw';
  ELSE
    ALTER ROLE kinetra LOGIN PASSWORD '$pw';
  END IF;
END `$`$;
"@
psql -U postgres -h localhost -v ON_ERROR_STOP=1 -c $sql
if ($LASTEXITCODE -ne 0) { Remove-Item Env:PGPASSWORD; throw "No se pudo crear el rol (¿contraseña correcta?)" }
foreach ($db in "kinetra","kinetra_test") {
  $exists = psql -U postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname='$db'"
  if (-not $exists) { psql -U postgres -h localhost -v ON_ERROR_STOP=1 -c "CREATE DATABASE $db OWNER kinetra ENCODING 'UTF8'" }
}
Remove-Item Env:PGPASSWORD

@"
KINETRA_DATABASE_URL=postgresql+psycopg://kinetra:$pw@localhost:5432/kinetra
KINETRA_TEST_DATABASE_URL=postgresql+psycopg://kinetra:$pw@localhost:5432/kinetra_test
KINETRA_SECRET_KEY=$secret
KINETRA_STORAGE_DIR=$root\storage
"@ | Set-Content -Encoding UTF8 $envFile
Write-Host "Listo: rol 'kinetra', bases 'kinetra' y 'kinetra_test', archivo .env creado."
