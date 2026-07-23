# start_master.ps1 — Startet den Orchestrator Master-Service
# Ausfuehren: powershell -ExecutionPolicy Bypass -File start_master.ps1

$ErrorActionPreference = "Stop"

# --------------------------------------------------------------------------
# Pfade
# --------------------------------------------------------------------------
$ProduktionRoot = "C:\Users\maxim\OneDrive\Desktop\Produktion"
$ReproCodeDir   = Join-Path $ProduktionRoot "Repro Code"
$AISystemeDir   = Join-Path $ProduktionRoot "AI Systeme"
$ArchivDir      = Join-Path $ProduktionRoot "Archiv"
$LogDir         = Join-Path $ArchivDir "logs"
$ConfigPath     = Join-Path $AISystemeDir "config.yaml"
$LogFile        = Join-Path $LogDir ("master_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")

# --------------------------------------------------------------------------
# Logging-Hilfsfunktion
# --------------------------------------------------------------------------
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts  = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    $line = "$ts | $Level | MASTER | $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

# --------------------------------------------------------------------------
# Voraussetzungen pruefen
# --------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Log "=== Master-Start ==="
Write-Log "Log-Datei: $LogFile"

# Python pruefen
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Log "Python nicht gefunden! Bitte Python 3.10+ installieren." "ERROR"
    exit 1
}
Write-Log "Python gefunden: $(python --version)"

# Config pruefen
if (-not (Test-Path $ConfigPath)) {
    Write-Log "config.yaml nicht gefunden: $ConfigPath" "ERROR"
    exit 1
}
Write-Log "Config gefunden: $ConfigPath"

# Netzwerk-Share pruefen
$SharePath = "\\server\produktion"
if (Test-Path $SharePath) {
    Write-Log "Netzwerk-Share erreichbar: $SharePath"
} else {
    Write-Log "Netzwerk-Share NICHT erreichbar: $SharePath — starte trotzdem (lokaler Modus)" "WARN"
}

# Archiv-Ordner anlegen
New-Item -ItemType Directory -Force -Path (Join-Path $ArchivDir "interactions") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ArchivDir "logs")         | Out-Null

# Abhaengigkeiten pruefen / installieren
Write-Log "Pruefe Python-Abhaengigkeiten..."
$ReqFile = Join-Path $ReproCodeDir "requirements.txt"
if (Test-Path $ReqFile) {
    python -m pip install -r $ReqFile --quiet
    Write-Log "Abhaengigkeiten installiert."
} else {
    Write-Log "requirements.txt nicht gefunden: $ReqFile" "WARN"
}

# --------------------------------------------------------------------------
# Orchestrator starten
# --------------------------------------------------------------------------
Write-Log "Starte Orchestrator auf Port 8000..."
$env:CONFIG_PATH = $ConfigPath

Set-Location $ReproCodeDir
$proc = Start-Process python `
    -ArgumentList "orchestrator.py" `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError  ($LogFile -replace "\.log$", "_err.log") `
    -PassThru `
    -NoNewWindow

Write-Log "Orchestrator gestartet (PID: $($proc.Id))"
Write-Log "Logs: $LogFile"
Write-Log "API:  http://localhost:8000"
Write-Log "Docs: http://localhost:8000/docs"

# PID speichern fuer spaeteres Stoppen
$PidFile = Join-Path $LogDir "master.pid"
$proc.Id | Set-Content $PidFile
Write-Log "PID gespeichert: $PidFile"
