# restart.ps1 — Reinicia o Orquestrador de Audio
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Reiniciando Orquestrador..." -ForegroundColor Cyan
& "$dir\stop.ps1"
Start-Sleep -Seconds 2
& "$dir\start.ps1"
