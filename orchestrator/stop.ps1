# stop.ps1 — Para API + Watcher
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path

foreach ($pidFile in @("$dir\.pid_api", "$dir\.pid_watcher")) {
    if (Test-Path $pidFile) {
        $p = Get-Content $pidFile -ErrorAction SilentlyContinue
        $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $p -Force
            Write-Host "Parado PID $p ($($proc.ProcessName))" -ForegroundColor Yellow
        }
        Remove-Item $pidFile -ErrorAction SilentlyContinue
    }
}
Write-Host "Orquestrador encerrado." -ForegroundColor Gray
