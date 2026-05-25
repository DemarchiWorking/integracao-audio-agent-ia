# ============================================================
#  connect-claude.ps1
#  DataDev Demarchi Lab - S10 FE + Windows 10
#  Verifica, instala e autentica o Claude Code CLI (plano Pro).
#  Uso: .\connect-claude.ps1  ou duplo clique em CONECTAR-CLAUDE.bat
# ============================================================
$ErrorActionPreference = 'SilentlyContinue'

function Write-OK   { param($m) Write-Host "  [OK] $m" -ForegroundColor Green  }
function Write-WARN { param($m) Write-Host "  [!!] $m" -ForegroundColor Yellow }
function Write-ERR  { param($m) Write-Host "  [XX] $m" -ForegroundColor Red    }
function Write-INFO { param($m) Write-Host "  >>  $m" -ForegroundColor Cyan    }
function Write-SEP  { Write-Host ('  ' + ('-' * 54)) -ForegroundColor DarkGray }
function Write-STEP { param($n,$t) Write-Host "  [$n] $t" -ForegroundColor White }

# ---- Banner -----------------------------------------------------------------
Clear-Host
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Cyan
Write-Host '   DataDev Demarchi Lab -- Conectar Claude Code CLI          ' -ForegroundColor Cyan
Write-Host ('   ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) -ForegroundColor Cyan
Write-Host '  ============================================================' -ForegroundColor Cyan
Write-Host ''

# ============================================================
# [1/3] LOCALIZAR / INSTALAR CLAUDE CLI
# ============================================================
Write-STEP '1/3' 'Verificando Claude Code CLI...'
Write-SEP

# Garantir que o diretorio npm global esta no PATH desta sessao
$npmBin = Join-Path $env:APPDATA 'npm'
if (Test-Path $npmBin) {
    if ($env:PATH -notlike "*$npmBin*") {
        $env:PATH = $npmBin + ';' + $env:PATH
    }
}

# Tentar encontrar o executavel
function Find-ClaudeExe {
    # 1. PATH
    $c = Get-Command claude   -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    $c = Get-Command claude.cmd -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    # 2. npm global (caminhos comuns)
    $candidates = @(
        (Join-Path $env:APPDATA  'npm\claude.cmd'),
        (Join-Path $env:APPDATA  'npm\claude'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Claude\claude.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\claude-code\claude.exe')
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

$claudeExe = Find-ClaudeExe

if (-not $claudeExe) {
    Write-WARN 'Claude Code CLI nao encontrado. Tentando instalar via npm...'
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npm) {
        Write-ERR 'npm nao encontrado no PATH.'
        Write-Host ''
        Write-Host '  Instale o Node.js (inclui npm) em: https://nodejs.org/' -ForegroundColor Yellow
        Write-Host '  Depois execute este arquivo novamente.' -ForegroundColor Yellow
        Write-Host ''
        Read-Host '  Pressione Enter para fechar'
        exit 1
    }
    Write-INFO 'Executando: npm install -g @anthropic-ai/claude-code ...'
    npm install -g '@anthropic-ai/claude-code' 2>&1 | Out-Null
    $claudeExe = Find-ClaudeExe
    if (-not $claudeExe) {
        Write-ERR 'Instalacao falhou. Tente manualmente:'
        Write-Host '     npm install -g @anthropic-ai/claude-code' -ForegroundColor Yellow
        Write-Host ''
        Read-Host '  Pressione Enter para fechar'
        exit 1
    }
    Write-OK "Claude Code CLI instalado: $claudeExe"
} else {
    $ver = (& $claudeExe --version 2>&1) | Select-Object -First 1
    Write-OK "Encontrado: $claudeExe"
    Write-OK "Versao:     $ver"
}
Write-Host ''

# ============================================================
# [2/3] VERIFICAR AUTENTICACAO
# ============================================================
Write-STEP '2/3' 'Verificando autenticacao...'
Write-SEP
Write-INFO 'Testando conectividade com Claude (aguarde alguns segundos)...'

$testResult = & $claudeExe -p 'responda apenas a palavra: AUTENTICADO' 2>&1
$authenticated = ($LASTEXITCODE -eq 0) -and ($testResult -notmatch 'Not logged in|login|Please run')

if ($authenticated) {
    Write-OK 'Autenticado com sucesso!'
    Write-OK "Resposta do Claude: $($testResult.ToString().Trim())"
    Write-Host ''
    Write-Host '  ============================================================' -ForegroundColor Green
    Write-Host '   CLAUDE CODE CLI PRONTO PARA USO                           ' -ForegroundColor Green
    Write-Host '  ============================================================' -ForegroundColor Green
    Write-Host ''
    Write-Host '   Motor ativo: Claude Code CLI (plano Pro)' -ForegroundColor Green
    Write-Host '   Sem necessidade de ANTHROPIC_API_KEY.' -ForegroundColor Green
    Write-Host ''
    Write-Host '   Proximos passos:' -ForegroundColor Cyan
    Write-Host '     1. Feche esta janela' -ForegroundColor White
    Write-Host '     2. Clique em INICIAR-INTEGRACAO.bat para iniciar o pipeline' -ForegroundColor White
    Write-Host '     3. Envie um audio pelo S10 via KDE Connect' -ForegroundColor White
    Write-Host ''
    Write-Host '  ============================================================' -ForegroundColor Green
    Write-Host ''
    Read-Host '  Pressione Enter para fechar'
    exit 0
}

# Nao autenticado
Write-WARN 'Nao autenticado ainda.'
if ($testResult) {
    $msg = ($testResult | Out-String).Trim()
    Write-Host "  Detalhe: $msg" -ForegroundColor DarkGray
}
Write-Host ''

# ============================================================
# [3/3] GUIA DE LOGIN
# ============================================================
Write-STEP '3/3' 'Iniciando processo de login...'
Write-SEP
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Yellow
Write-Host '   SIGA ESTES PASSOS NA JANELA QUE VAI ABRIR:               ' -ForegroundColor Yellow
Write-Host '  ============================================================' -ForegroundColor Yellow
Write-Host ''
Write-Host '   Passo 1: Aguarde o Claude Code carregar' -ForegroundColor White
Write-Host '            (voce vera um prompt de entrada de texto)' -ForegroundColor DarkGray
Write-Host ''
Write-Host '   Passo 2: Digite exatamente:   /login' -ForegroundColor Cyan
Write-Host '            Depois pressione:    Enter' -ForegroundColor DarkGray
Write-Host ''
Write-Host '   Passo 3: O NAVEGADOR vai abrir automaticamente' -ForegroundColor White
Write-Host '            Entre com a conta do seu plano Claude Pro' -ForegroundColor DarkGray
Write-Host ''
Write-Host '   Passo 4: Volte para este terminal' -ForegroundColor White
Write-Host '            O login sera confirmado aqui' -ForegroundColor DarkGray
Write-Host ''
Write-Host '   Passo 5: Para sair do Claude Code:  /exit  ou  Ctrl+C' -ForegroundColor White
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Yellow
Write-Host ''

$resp = Read-Host '  Pressione Enter para abrir o Claude Code e fazer login (ou S para sair)'
if ($resp -eq 'S' -or $resp -eq 's') {
    Write-WARN 'Saindo sem autenticar. Execute este arquivo novamente quando quiser autenticar.'
    Write-Host ''
    Read-Host '  Pressione Enter para fechar'
    exit 0
}

# Abrir claude interativo NESTA janela
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Cyan
Write-Host '   CLAUDE CODE -- MODO INTERATIVO                            ' -ForegroundColor Cyan
Write-Host '   LEMBRE: digite /login e pressione Enter                  ' -ForegroundColor Yellow
Write-Host '  ============================================================' -ForegroundColor Cyan
Write-Host ''
Start-Sleep -Seconds 1

# Executar claude interativo (toma conta do terminal ate o usuario sair)
& $claudeExe

# --- Volta aqui depois que o usuario sair do claude ---
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Cyan
Write-Host '   Verificando autenticacao pos-login...' -ForegroundColor Cyan
Write-Host '  ============================================================' -ForegroundColor Cyan
Write-Host ''
Start-Sleep -Seconds 2

$testResult2  = & $claudeExe -p 'responda apenas a palavra: AUTENTICADO' 2>&1
$authenticated2 = ($LASTEXITCODE -eq 0) -and ($testResult2 -notmatch 'Not logged in|login|Please run')

if ($authenticated2) {
    Write-Host ''
    Write-Host '  ============================================================' -ForegroundColor Green
    Write-Host '   LOGIN REALIZADO COM SUCESSO!                              ' -ForegroundColor Green
    Write-Host '  ============================================================' -ForegroundColor Green
    Write-Host ''
    Write-OK "Motor ativo: Claude Code CLI (plano Pro)"
    Write-OK "Pipeline pronto. Clique em INICIAR-INTEGRACAO.bat para comecar."
    Write-Host ''
    Write-Host '   Fluxo completo:' -ForegroundColor Cyan
    Write-Host '     S10 envia audio -> Whisper transcreve -> Claude Pro processa' -ForegroundColor White
    Write-Host '     -> P1/P2/P3 priorizados -> executa no Windows -> salva resultado' -ForegroundColor White
    Write-Host ''
    Write-Host '  ============================================================' -ForegroundColor Green
} else {
    Write-Host ''
    Write-Host '  ============================================================' -ForegroundColor Red
    Write-Host '   Autenticacao nao detectada apos o login.                  ' -ForegroundColor Red
    Write-Host '  ============================================================' -ForegroundColor Red
    Write-Host ''
    Write-ERR 'O login pode nao ter sido completado corretamente.'
    Write-Host ''
    Write-Host '   Tente manualmente:' -ForegroundColor Yellow
    Write-Host ''
    Write-Host '   1. Abra um novo PowerShell e execute:' -ForegroundColor White
    Write-Host "        & '$claudeExe'" -ForegroundColor DarkGray
    Write-Host ''
    Write-Host '   2. Dentro do Claude Code, execute:' -ForegroundColor White
    Write-Host '        /login' -ForegroundColor DarkGray
    Write-Host ''
    Write-Host '   3. Complete o login no navegador com sua conta Claude Pro' -ForegroundColor White
    Write-Host ''
    Write-Host '   4. Execute este arquivo novamente para verificar.' -ForegroundColor White
    Write-Host ''
    Write-Host '   Se o problema persistir:' -ForegroundColor Yellow
    Write-Host '     https://claude.ai/download  (reinstalar Claude Code)' -ForegroundColor DarkGray
    Write-Host ''
    Write-Host '  ============================================================' -ForegroundColor Red
}

Write-Host ''
Read-Host '  Pressione Enter para fechar'
