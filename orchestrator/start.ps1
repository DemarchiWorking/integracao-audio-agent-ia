# start.ps1 — Inicia Orquestrador (API) + Watcher (KDE Connect bridge)
# DataDev Demarchi Lab — Audio Orchestrator v1.0.0

$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidApi     = "$dir\.pid_api"
$pidWatcher = "$dir\.pid_watcher"

function Is-Running($pidFile) {
    if (-not (Test-Path $pidFile)) { return $false }
    $p = Get-Content $pidFile -ErrorAction SilentlyContinue
    return ($null -ne (Get-Process -Id $p -ErrorAction SilentlyContinue))
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DataDev Lab -- Audio Orchestrator v1.0.0" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# --- API (FastAPI) ---
if (Is-Running $pidApi) {
    $p = Get-Content $pidApi
    Write-Host "[API]     Ja rodando (PID $p)" -ForegroundColor Yellow
} else {
    $proc = Start-Process python -ArgumentList "main.py" `
        -WorkingDirectory $dir -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput "$dir\api.log" `
        -RedirectStandardError  "$dir\api_err.log"
    $proc.Id | Out-File $pidApi -Encoding ascii
    Write-Host "[API]     Iniciado  (PID $($proc.Id))  porta 8765" -ForegroundColor Green
}

Start-Sleep -Seconds 3  # aguarda API subir antes do watcher

# --- Watcher (KDE Connect bridge) ---
if (Is-Running $pidWatcher) {
    $p = Get-Content $pidWatcher
    Write-Host "[Watcher] Ja rodando (PID $p)" -ForegroundColor Yellow
} else {
    $proc = Start-Process python -ArgumentList "watcher.py" `
        -WorkingDirectory $dir -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput "$dir\watcher.log" `
        -RedirectStandardError  "$dir\watcher_err.log"
    $proc.Id | Out-File $pidWatcher -Encoding ascii
    Write-Host "[Watcher] Iniciado  (PID $($proc.Id))  monitorando KDE Connect" -ForegroundColor Green
}

Write-Host ""
Write-Host "Health : http://localhost:8765/health" -ForegroundColor Gray
Write-Host "Status : http://localhost:8765/status" -ForegroundColor Gray
Write-Host "Inbox  : $dir\..\inbox_tarefas\" -ForegroundColor Gray
Write-Host "Logs   : $dir\api.log | watcher.log" -ForegroundColor Gray
Write-Host ""
Write-Host "Para parar: .\stop.ps1" -ForegroundColor DarkGray
