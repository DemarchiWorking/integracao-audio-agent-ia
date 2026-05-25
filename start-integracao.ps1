# ============================================================
#  start-integracao.ps1
#  DataDev Demarchi Lab - S10 FE + Windows 10
#  Inicia e valida toda a integracao de audio.
#  Uso: .\start-integracao.ps1
# ============================================================
$ErrorActionPreference = 'SilentlyContinue'

$ROOT        = Split-Path -Parent $MyInvocation.MyCommand.Path
$ORCH        = Join-Path $ROOT 'orchestrator'
$PID_API     = Join-Path $ORCH '.pid_api'
$PID_WATCHER = Join-Path $ORCH '.pid_watcher'
$LOG_API     = Join-Path $ORCH 'api_err.log'
$LOG_WATCHER = Join-Path $ORCH 'watcher_err.log'
$KDE_DIR     = Join-Path $env:USERPROFILE 'Documents\KDE Connect'
$KDE_DAEMON  = Join-Path $env:LOCALAPPDATA 'Programs\KDE Connect\bin\kdeconnectd.exe'
$KDE_IND     = Join-Path $env:LOCALAPPDATA 'Programs\KDE Connect\bin\kdeconnect-indicator.exe'
$KDE_CLI     = Join-Path $env:LOCALAPPDATA 'Programs\KDE Connect\bin\kdeconnect-cli.exe'
$FFMPEG_DIR  = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links'
$API_URL     = 'http://localhost:8765'

function Write-OK   { param($m) Write-Host "  [OK] $m" -ForegroundColor Green  }
function Write-WARN { param($m) Write-Host "  [!!] $m" -ForegroundColor Yellow }
function Write-ERR  { param($m) Write-Host "  [XX] $m" -ForegroundColor Red    }
function Write-SEP  { Write-Host ('  ' + ('-' * 54)) -ForegroundColor DarkGray }

function Is-ProcRunning {
    param([string]$pidFile)
    if (-not (Test-Path $pidFile)) { return $false }
    $id = Get-Content $pidFile -ErrorAction SilentlyContinue
    if (-not $id) { return $false }
    return ($null -ne (Get-Process -Id ([int]$id) -ErrorAction SilentlyContinue))
}

function Wait-ForAPI {
    param([int]$Secs = 25)
    for ($i = 1; $i -le $Secs; $i++) {
        Start-Sleep -Seconds 1
        # Le o log da API: uvicorn escreve "startup complete" quando pronto
        $tail = Get-Content $LOG_API -Tail 5 -ErrorAction SilentlyContinue
        $ready = $tail | Where-Object { $_ -match 'startup complete|Uvicorn running' }
        if ($ready) { return $true }
        if ($i % 5 -eq 0) {
            Write-Host "  >> Aguardando API... ${i}s/${Secs}s (Whisper carregando modelo base)" -ForegroundColor DarkGray
        }
    }
    return $false
}

# ---- Banner -----------------------------------------------------------------
Clear-Host
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Cyan
Write-Host '   DataDev Demarchi Lab -- Integracao S10 FE + Windows 10    ' -ForegroundColor Cyan
Write-Host ('   ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '   v1.0.0') -ForegroundColor Cyan
Write-Host '  ============================================================' -ForegroundColor Cyan
Write-Host ''

# ============================================================
# [1/5] PRE-REQUISITOS
# ============================================================
Write-Host '  [1/5] Verificando pre-requisitos...' -ForegroundColor White
Write-SEP
$allOk = $true

# Python
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pyCmd) {
    $pyVer = python --version 2>&1
    Write-OK "Python: $pyVer"
} else {
    Write-ERR 'Python nao encontrado no PATH'
    $allOk = $false
}

# FFmpeg
$ffExe = Join-Path $FFMPEG_DIR 'ffmpeg.exe'
if (Test-Path $ffExe) {
    Write-OK "FFmpeg: $ffExe"
    if ($env:PATH -notlike "*$FFMPEG_DIR*") {
        $env:PATH = $FFMPEG_DIR + ';' + $env:PATH
    }
} else {
    Write-WARN 'FFmpeg nao encontrado em WinGet Links'
    Write-WARN 'Instale: winget install Gyan.FFmpeg'
}

# Pacotes Python - verificar cada um
$pkgList = @('whisper','fastapi','uvicorn','watchdog','anthropic')
foreach ($pkg in $pkgList) {
    $result = python -c "import $pkg; print('ok')" 2>&1
    if ($result -like '*ok*') {
        Write-OK "pip pkg: $pkg"
    } else {
        if ($pkg -eq 'anthropic') {
            Write-WARN "pip pkg: $pkg -- NAO instalado (pip install anthropic)"
        } else {
            Write-ERR "pip pkg: $pkg -- NAO instalado (pip install $pkg)"
            $allOk = $false
        }
    }
}

# API Key
if ($env:ANTHROPIC_API_KEY -and $env:ANTHROPIC_API_KEY.Length -gt 10) {
    $masked = $env:ANTHROPIC_API_KEY.Substring(0, 14) + '...'
    Write-OK "ANTHROPIC_API_KEY: $masked"
} else {
    Write-WARN 'ANTHROPIC_API_KEY: NAO configurada'
    Write-WARN '  Execute: [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY","sk-ant-...","User")'
}

# Arquivos do orquestrador
$requiredFiles = @('main.py','watcher.py','processar_com_claude.py','config.py','packet_generator.py')
foreach ($f in $requiredFiles) {
    $fPath = Join-Path $ORCH $f
    if (Test-Path $fPath) {
        Write-OK "Arquivo: orchestrator\$f"
    } else {
        Write-ERR "AUSENTE: orchestrator\$f"
        $allOk = $false
    }
}

if (-not $allOk) {
    Write-Host ''
    Write-ERR 'Pre-requisitos criticos ausentes. Corrija os erros e tente novamente.'
    Write-Host ''
    exit 1
}
Write-Host ''

# ============================================================
# [2/5] KDE CONNECT
# ============================================================
Write-Host '  [2/5] Verificando KDE Connect...' -ForegroundColor White
Write-SEP

$daemon = Get-Process -Name 'kdeconnectd' -ErrorAction SilentlyContinue
if ($daemon) {
    Write-OK "kdeconnectd: rodando PID $($daemon.Id)"
} else {
    if (Test-Path $KDE_DAEMON) {
        Write-Host '  >> Iniciando kdeconnectd...' -ForegroundColor Cyan
        Start-Process -FilePath $KDE_DAEMON -WindowStyle Hidden
        Start-Sleep -Seconds 2
        $daemon = Get-Process -Name 'kdeconnectd' -ErrorAction SilentlyContinue
        if ($daemon) {
            Write-OK "kdeconnectd: iniciado PID $($daemon.Id)"
        } else {
            Write-WARN 'kdeconnectd: ainda subindo, pode demorar alguns segundos'
        }
    } else {
        Write-WARN "kdeconnectd.exe nao encontrado em: $KDE_DAEMON"
        Write-WARN 'Instale: winget install KDE.KDEConnect'
    }
}

$indicator = Get-Process -Name 'kdeconnect-indicator' -ErrorAction SilentlyContinue
if ($indicator) {
    Write-OK "kdeconnect-indicator: rodando PID $($indicator.Id)"
} else {
    if (Test-Path $KDE_IND) {
        Start-Process -FilePath $KDE_IND -WindowStyle Hidden
        Start-Sleep -Seconds 1
        Write-OK 'kdeconnect-indicator: iniciado'
    }
}

if (Test-Path $KDE_DIR) {
    $nFiles = (Get-ChildItem $KDE_DIR -ErrorAction SilentlyContinue).Count
    Write-OK "Pasta monitorada: $KDE_DIR  [$nFiles arquivos]"
} else {
    New-Item -ItemType Directory -Path $KDE_DIR -Force | Out-Null
    Write-OK "Pasta criada: $KDE_DIR"
}

if (Test-Path $KDE_CLI) {
    $devOut = (& $KDE_CLI --list-devices 2>&1) | Out-String
    if ($devOut -match 'Samsung|S10|Android|phone') {
        Write-OK "Dispositivo pareado: $($devOut.Trim())"
    } else {
        Write-WARN 'Nenhum dispositivo Samsung pareado detectado'
        Write-WARN 'Abra KDE Connect no S10 FE -> toque em DESKTOP-N3BPMC5'
    }
} else {
    Write-WARN "kdeconnect-cli nao encontrado: $KDE_CLI"
}
Write-Host ''

# ============================================================
# [3/5] ORQUESTRADOR API
# ============================================================
Write-Host '  [3/5] Iniciando Orquestrador API porta 8765...' -ForegroundColor White
Write-SEP

if (Is-ProcRunning $PID_API) {
    $existingPid = Get-Content $PID_API
    Write-OK "API: ja rodando PID $existingPid -- mantendo"
} else {
    Remove-Item $PID_API -ErrorAction SilentlyContinue
    $apiLog    = Join-Path $ORCH 'api.log'
    $apiLogErr = $LOG_API

    $proc = Start-Process python -ArgumentList 'main.py' `
        -WorkingDirectory $ORCH -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $apiLog `
        -RedirectStandardError  $apiLogErr

    $proc.Id | Out-File $PID_API -Encoding ascii
    Write-Host "  >> Aguardando API subir PID $($proc.Id)..." -ForegroundColor Cyan

    $up = Wait-ForAPI -Secs 25
    if ($up) {
        Write-OK "API: pronta em $API_URL PID $($proc.Id)"
    } else {
        Write-ERR "API nao respondeu em 25s -- log:"
        Get-Content $apiLogErr -Tail 6 -ErrorAction SilentlyContinue |
            ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed }
        Write-Host ''
        exit 1
    }
}
Write-Host ''

# ============================================================
# [4/5] WATCHER
# ============================================================
Write-Host '  [4/5] Iniciando Watcher monitor KDE Connect...' -ForegroundColor White
Write-SEP

if (Is-ProcRunning $PID_WATCHER) {
    $existingPid = Get-Content $PID_WATCHER
    Write-OK "Watcher: ja rodando PID $existingPid -- mantendo"
} else {
    Remove-Item $PID_WATCHER -ErrorAction SilentlyContinue
    $watLog    = Join-Path $ORCH 'watcher.log'
    $watLogErr = $LOG_WATCHER

    $proc = Start-Process python -ArgumentList 'watcher.py' `
        -WorkingDirectory $ORCH -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $watLog `
        -RedirectStandardError  $watLogErr

    $proc.Id | Out-File $PID_WATCHER -Encoding ascii
    Start-Sleep -Seconds 2

    $logLines = Get-Content $watLogErr -Tail 4 -ErrorAction SilentlyContinue
    $isReady  = $logLines | Where-Object { $_ -match 'Aguardando|pronto|watcher' }
    if ($isReady) {
        Write-OK "Watcher: ativo e monitorando PID $($proc.Id)"
    } else {
        Write-OK "Watcher: iniciado PID $($proc.Id)"
    }
}
Write-Host ''

# ============================================================
# [5/5] VALIDACAO FINAL
# ============================================================
Write-Host '  [5/5] Validacao final do sistema...' -ForegroundColor White
Write-SEP

# Health check
try {
    $healthUrl  = $API_URL + '/health'
    $healthResp = (Invoke-WebRequest $healthUrl -UseBasicParsing -TimeoutSec 5).Content | ConvertFrom-Json
    Write-OK "Health: status=$($healthResp.status)  versao=$($healthResp.version)"
} catch {
    Write-ERR 'Health check falhou -- API nao responde'
}

# Status
try {
    $statusUrl  = $API_URL + '/status'
    $statusResp = (Invoke-WebRequest $statusUrl -UseBasicParsing -TimeoutSec 5).Content | ConvertFrom-Json
    $stats = $statusResp.stats
    Write-OK "Backend STT: $($statusResp.backend_stt)"
    Write-OK "Stats: recebidos=$($stats.received)  processados=$($stats.processed)  erros=$($stats.errors)"
} catch {
    Write-WARN 'Status endpoint nao respondeu'
}

# Inbox
$inbox = Join-Path $ROOT 'inbox_tarefas'
if (Test-Path $inbox) {
    $packets = (Get-ChildItem $inbox -Directory -ErrorAction SilentlyContinue).Count
    Write-OK "Pacotes em inbox_tarefas: $packets"
    if ($packets -gt 0) {
        $lastPkt = (Get-ChildItem $inbox -Directory |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1).Name
        Write-OK "Ultimo pacote: $lastPkt"
    }
}

$finalApiPid     = Get-Content $PID_API     -ErrorAction SilentlyContinue
$finalWatcherPid = Get-Content $PID_WATCHER -ErrorAction SilentlyContinue
$finalKdePid     = (Get-Process -Name 'kdeconnectd' -ErrorAction SilentlyContinue).Id

# ---- Resumo final -----------------------------------------------------------
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Green
Write-Host '   SISTEMA PRONTO                                             ' -ForegroundColor Green
Write-Host '  ============================================================' -ForegroundColor Green
Write-Host ''
Write-Host '   SERVICOS ATIVOS:' -ForegroundColor White
Write-Host "     API FastAPI   http://localhost:8765   PID $finalApiPid" -ForegroundColor Green
Write-Host "     Watcher       monitorando KDE Connect  PID $finalWatcherPid" -ForegroundColor Green
Write-Host "     KDE Connect   bridge WiFi S10 FE       PID $finalKdePid" -ForegroundColor Green
Write-Host ''
Write-Host '   IP DO PC para informar ao S10 FE: 192.168.3.65' -ForegroundColor Yellow
Write-Host "   PASTA MONITORADA: $KDE_DIR" -ForegroundColor Yellow
Write-Host ''
Write-Host '   PROXIMOS PASSOS NO S10 FE:' -ForegroundColor Cyan
Write-Host '     1. Abra o app KDE Connect' -ForegroundColor White
Write-Host '     2. Toque em DESKTOP-N3BPMC5' -ForegroundColor White
Write-Host '     3. Grave audio no Gravador de Voz Samsung' -ForegroundColor White
Write-Host '     4. KDE Connect -> Enviar arquivos -> selecione a gravacao' -ForegroundColor White
Write-Host ''
Write-Host '   MONITORAR EM TEMPO REAL:' -ForegroundColor Cyan
Write-Host "     Get-Content '$LOG_WATCHER' -Wait -Tail 5" -ForegroundColor DarkGray
Write-Host "     Get-Content '$LOG_API'     -Wait -Tail 5" -ForegroundColor DarkGray
Write-Host ''
Write-Host '   PROCESSAR COM CLAUDE apos receber audio:' -ForegroundColor Cyan
$processorPath = Join-Path $ORCH 'processar_com_claude.py'
Write-Host "     python '$processorPath'" -ForegroundColor DarkGray
Write-Host ''
Write-Host '   PARAR TUDO:' -ForegroundColor Cyan
Write-Host '     .\stop-integracao.ps1' -ForegroundColor DarkGray
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Green
Write-Host ''
