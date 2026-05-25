# ============================================================
#  stop-integracao.ps1
#  DataDev Demarchi Lab - S10 FE + Windows 10
#  Para todos os servicos da integracao com seguranca.
#  Exibe estatisticas da sessao antes de encerrar.
#  Uso: .\stop-integracao.ps1
# ============================================================
$ErrorActionPreference = 'SilentlyContinue'

$ROOT        = Split-Path -Parent $MyInvocation.MyCommand.Path
$ORCH        = Join-Path $ROOT 'orchestrator'
$PID_API     = Join-Path $ORCH '.pid_api'
$PID_WATCHER = Join-Path $ORCH '.pid_watcher'
$LOG_API     = Join-Path $ORCH 'api_err.log'
$LOG_WATCHER = Join-Path $ORCH 'watcher_err.log'
$API_URL     = 'http://localhost:8765'

function Write-OK   { param($m) Write-Host "  [OK] $m" -ForegroundColor Green  }
function Write-WARN { param($m) Write-Host "  [--] $m" -ForegroundColor Yellow }
function Write-ERR  { param($m) Write-Host "  [XX] $m" -ForegroundColor Red    }
function Write-SEP  { Write-Host ('  ' + ('-' * 54)) -ForegroundColor DarkGray }

function Stop-OrchestratorService {
    param([string]$pidFile, [string]$label)

    if (-not (Test-Path $pidFile)) {
        Write-WARN "$label -- sem PID registrado, ja estava parado"
        return
    }

    $procId = Get-Content $pidFile -ErrorAction SilentlyContinue
    if (-not $procId) {
        Write-WARN "$label -- PID file vazio"
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        return
    }

    $proc = Get-Process -Id ([int]$procId) -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id ([int]$procId) -Force
        Start-Sleep -Milliseconds 600
        $confirm = Get-Process -Id ([int]$procId) -ErrorAction SilentlyContinue
        if ($confirm) {
            Write-WARN "$label -- processo ainda ativo apos Stop-Process"
        } else {
            Write-OK "$label -- parado PID $procId"
        }
    } else {
        Write-WARN "$label -- PID $procId nao estava rodando"
    }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

# ---- Banner -----------------------------------------------------------------
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor DarkCyan
Write-Host '   DataDev Demarchi Lab -- Stop Integracao                   ' -ForegroundColor DarkCyan
Write-Host ('   ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '   v1.0.0') -ForegroundColor DarkCyan
Write-Host '  ============================================================' -ForegroundColor DarkCyan
Write-Host ''

# ============================================================
# [1/3] ESTATISTICAS DA SESSAO
# ============================================================
Write-Host '  [1/3] Coletando estatisticas da sessao...' -ForegroundColor White
Write-SEP

try {
    $statusUrl  = $API_URL + '/status'
    $statusResp = (Invoke-WebRequest $statusUrl -UseBasicParsing -TimeoutSec 3).Content | ConvertFrom-Json
    $stats = $statusResp.stats
    Write-OK "Sessao iniciada : $($stats.started_at)"
    Write-OK "Audios recebidos: $($stats.received)"
    Write-OK "Pacotes gerados : $($stats.processed)"
    if ($stats.errors -gt 0) {
        Write-WARN "Erros na sessao : $($stats.errors)"
    } else {
        Write-OK "Erros na sessao : 0"
    }
} catch {
    Write-WARN 'API nao responde -- estatisticas indisponiveis'
}

# Pacotes em inbox_tarefas
$inbox = Join-Path $ROOT 'inbox_tarefas'
if (Test-Path $inbox) {
    $allPkts = Get-ChildItem $inbox -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
    Write-OK "Total pacotes em inbox_tarefas: $($allPkts.Count)"
    if ($allPkts.Count -gt 0) {
        Write-OK "Ultimo pacote: $($allPkts[0].Name)"
    }
}

# Linhas de log geradas nesta sessao
foreach ($logFile in @($LOG_API, $LOG_WATCHER)) {
    if (Test-Path $logFile) {
        $lineCount = (Get-Content $logFile -ErrorAction SilentlyContinue).Count
        $logName   = Split-Path $logFile -Leaf
        Write-OK "Log $logName -- $lineCount linhas"
    }
}
Write-Host ''

# ============================================================
# [2/3] PARAR SERVICOS
# ============================================================
Write-Host '  [2/3] Parando servicos...' -ForegroundColor White
Write-SEP

# Parar watcher primeiro, depois API
Stop-OrchestratorService -pidFile $PID_WATCHER -label 'Watcher    '
Stop-OrchestratorService -pidFile $PID_API     -label 'API FastAPI'

# Verificar processos orfaos (main.py ou watcher.py ainda rodando)
$orphans = Get-WmiObject Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq 'python.exe' -and ($_.CommandLine -match 'main\.py|watcher\.py') }

if ($orphans) {
    foreach ($o in $orphans) {
        Stop-Process -Id $o.ProcessId -Force -ErrorAction SilentlyContinue
        Write-WARN "Processo orfao encerrado: PID $($o.ProcessId)"
    }
} else {
    Write-OK 'Nenhum processo orfao encontrado'
}

# Checar se porta 8765 foi liberada
Start-Sleep -Milliseconds 800
$portFree = $false
try {
    Invoke-WebRequest ($API_URL + '/health') -UseBasicParsing -TimeoutSec 2 | Out-Null
} catch {
    $portFree = $true
}
if ($portFree) {
    Write-OK 'Porta 8765: liberada'
} else {
    Write-WARN 'Porta 8765: ainda em uso, aguarde alguns segundos'
}
Write-Host ''

# ============================================================
# [3/3] STATUS FINAL E PACOTES PENDENTES
# ============================================================
Write-Host '  [3/3] Status final...' -ForegroundColor White
Write-SEP

Write-OK 'API FastAPI: PARADA'
Write-OK 'Watcher:     PARADO'

$kdePid = (Get-Process -Name 'kdeconnectd' -ErrorAction SilentlyContinue).Id
if ($kdePid) {
    Write-OK "KDE Connect: rodando PID $kdePid -- mantido para nao perder pareamento"
} else {
    Write-WARN 'KDE Connect: nao detectado'
}

# Mostrar pacotes pendentes de processamento
Write-Host ''
if (Test-Path $inbox) {
    $allPkts = Get-ChildItem $inbox -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
    if ($allPkts.Count -gt 0) {
        Write-Host '   PACOTES DISPONIVEIS PARA PROCESSAR COM CLAUDE:' -ForegroundColor Yellow
        $shown = $allPkts | Select-Object -First 5
        foreach ($pkt in $shown) {
            $hasResp = Test-Path (Join-Path $pkt.FullName 'resposta_claude.md')
            if ($hasResp) {
                Write-Host "     [processado] $($pkt.Name)" -ForegroundColor DarkGray
            } else {
                Write-Host "     [pendente]   $($pkt.Name)" -ForegroundColor Yellow
            }
        }
        if ($allPkts.Count -gt 5) {
            $remaining = $allPkts.Count - 5
            Write-Host "     ... e mais $remaining pacotes" -ForegroundColor DarkGray
        }
        Write-Host ''
        Write-Host '   Para processar o mais recente:' -ForegroundColor Cyan
        $processorPath = Join-Path $ORCH 'processar_com_claude.py'
        Write-Host "     python '$processorPath'" -ForegroundColor DarkGray
    }
}

# ---- Resumo -----------------------------------------------------------------
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor DarkCyan
Write-Host '   INTEGRACAO ENCERRADA                                       ' -ForegroundColor DarkCyan
Write-Host '  ============================================================' -ForegroundColor DarkCyan
Write-Host ''
Write-Host '   Para reiniciar:' -ForegroundColor Cyan
Write-Host '     .\start-integracao.ps1' -ForegroundColor DarkGray
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor DarkCyan
Write-Host ''
