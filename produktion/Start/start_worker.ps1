# start_worker.ps1 — Startet eine Worker-Instanz
# Ausfuehren: powershell -ExecutionPolicy Bypass -File start_worker.ps1 -WorkerId worker_1 -Port 8001
# 
# Parameter:
#   -WorkerId   ID des Workers (worker_1 bis worker_7)
#   -Port       API-Port des Workers (8001-8007)
#   -MasterHost IP/Hostname des Master-Services (default: localhost)

param(
    [Parameter(Mandatory=$true)]
    [string]$WorkerId,

    [Parameter(Mandatory=$true)]
    [int]$Port,

    [string]$MasterHost = "localhost",
    [int]$MasterPort    = 8000
)

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
$LogFile        = Join-Path $LogDir ("${WorkerId}_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")

# --------------------------------------------------------------------------
# Logging-Hilfsfunktion
# --------------------------------------------------------------------------
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts   = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    $line = "$ts | $Level | $WorkerId | $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

# --------------------------------------------------------------------------
# Voraussetzungen pruefen
# --------------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Log "=== Worker-Start: $WorkerId ==="
Write-Log "Port: $Port | Master: ${MasterHost}:${MasterPort}"
Write-Log "Log-Datei: $LogFile"

# Python pruefen
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Log "Python nicht gefunden!" "ERROR"
    exit 1
}
Write-Log "Python: $(python --version)"

# Ollama pruefen
$OllamaUrl = "http://localhost:11434/api/tags"
try {
    $resp = Invoke-WebRequest -Uri $OllamaUrl -TimeoutSec 5 -UseBasicParsing
    Write-Log "Ollama erreichbar: $OllamaUrl"
} catch {
    Write-Log "Ollama NICHT erreichbar ($OllamaUrl) — starte trotzdem" "WARN"
    Write-Log "Starte Ollama..." "WARN"
    Start-Process ollama -ArgumentList "serve" -NoNewWindow
    Start-Sleep -Seconds 3
}

# Netzwerk-Share pruefen
$SharePath = "\\server\produktion"
if (Test-Path $SharePath) {
    Write-Log "Netzwerk-Share erreichbar: $SharePath"
} else {
    Write-Log "Netzwerk-Share NICHT erreichbar: $SharePath (lokaler Modus)" "WARN"
}

# Config pruefen
if (-not (Test-Path $ConfigPath)) {
    Write-Log "config.yaml nicht gefunden: $ConfigPath" "ERROR"
    exit 1
}

# Abhaengigkeiten
$ReqFile = Join-Path $ReproCodeDir "requirements.txt"
if (Test-Path $ReqFile) {
    python -m pip install -r $ReqFile --quiet
    Write-Log "Abhaengigkeiten OK."
}

# --------------------------------------------------------------------------
# Worker starten
# --------------------------------------------------------------------------
Write-Log "Starte Worker $WorkerId auf Port $Port..."

$env:CONFIG_PATH = $ConfigPath
$env:WORKER_ID   = $WorkerId
$env:WORKER_PORT = $Port.ToString()

Set-Location $ReproCodeDir
$proc = Start-Process python `
    -ArgumentList "worker.py" `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError  ($LogFile -replace "\.log$", "_err.log") `
    -PassThru `
    -NoNewWindow

Write-Log "Worker gestartet (PID: $($proc.Id))"
Write-Log "API:  http://localhost:$Port"
Write-Log "Docs: http://localhost:$Port/docs"

# PID speichern
$PidFile = Join-Path $LogDir "${WorkerId}.pid"
$proc.Id | Set-Content $PidFile

# --------------------------------------------------------------------------
# Beim Master registrieren
# --------------------------------------------------------------------------
Start-Sleep -Seconds 5  # Warte bis Worker bereit
$MasterUrl = "http://${MasterHost}:${MasterPort}"
Write-Log "Pruefe Master-Verbindung: $MasterUrl..."
try {
    $health = Invoke-WebRequest -Uri "$MasterUrl/health" -TimeoutSec 5 -UseBasicParsing
    Write-Log "Master erreichbar. Worker $WorkerId laeuft."
} catch {
    Write-Log "Master nicht erreichbar ($MasterUrl) — Worker laeuft im Standalone-Modus" "WARN"
}

Write-Log "=== Worker $WorkerId bereit ==="
