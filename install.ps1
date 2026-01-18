# Pokretanje:
# powershell -ExecutionPolicy RemoteSigned -File install.ps1

# opcija 2 je da se pozicionirate u root folder te napisete sljedece 2 linije:
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
# .\install.ps1

Write-Host "=== Temporal Worktime App Installer ==="

Set-Location $PSScriptRoot

function Require-Command($cmd, $name) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "$name nije instaliran ili nije u PATH-u."
        exit 1
    }
}

Require-Command "python" "Python"
Require-Command "psql" "PostgreSQL (psql)"

Write-Host "Provjeravam PostgreSQL servis..."

$pgService = Get-Service | Where-Object {
    $_.Name -like "postgresql*" -or $_.DisplayName -like "PostgreSQL*"
} | Select-Object -First 1

if (-not $pgService) {
    Write-Error "PostgreSQL servis nije pronađen. Instaliraj PostgreSQL."
    exit 1
}

if ($pgService.Status -ne "Running") {
    Write-Host "Pokrećem PostgreSQL servis ($($pgService.Name))..."
    Start-Service $pgService.Name
    Start-Sleep -Seconds 5
} else {
    Write-Host "PostgreSQL servis je već pokrenut."
}

if (-not (Test-Path ".env")) {
    Write-Error ".env datoteka ne postoji."
    exit 1
}

Write-Host "Učitavam .env konfiguraciju..."

$envLines = Get-Content ".env" | Where-Object {
    $_ -and $_ -notmatch "^#"
}

foreach ($line in $envLines) {
    $key, $value = $line -split "=", 2
    Set-Variable -Name $key -Value $value
}

$env:PGPASSWORD = $DB_PASS

Write-Host "DB_HOST=$DB_HOST"
Write-Host "DB_PORT=$DB_PORT"
Write-Host "DB_NAME=$DB_NAME"

if (-not (Test-Path "venv")) {
    Write-Host "Kreiram virtualno okruženje..."
    python -m venv venv
}

Write-Host "Aktiviram virtualno okruženje..."
.\venv\Scripts\Activate.ps1

Write-Host "Instaliram Python zavisnosti..."
python -m pip install --upgrade pip

pip uninstall -y PySimpleGUI | Out-Null
pip cache purge | Out-Null
pip install --upgrade --extra-index-url https://PySimpleGUI.net/install PySimpleGUI

pip install -r requirements.txt

Write-Host "Provjeravam konekciju na PostgreSQL..."

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "\q"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ne mogu se spojiti na PostgreSQL."
    exit 1
}

Write-Host "Provjeravam postoji li baza..."

$dbExists = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -t `
-c "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';"

if ($dbExists -notmatch "1") {
    Write-Host "Kreiram bazu $DB_NAME..."
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres `
    -c "CREATE DATABASE $DB_NAME;"
} else {
    Write-Host "Baza već postoji."
}

Write-Host "Pokrećem inicijalni SQL..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME `
-f ".\db\baza.sql"

Write-Host "Pokrećem aplikaciju..."
python main.py
