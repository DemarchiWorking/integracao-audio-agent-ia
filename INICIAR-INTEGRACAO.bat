@echo off
title DataDev Lab - Iniciando Integracao...
chcp 65001 > nul

:: ================================================================
::  INICIAR-INTEGRACAO.bat  v2.1
::  DataDev Demarchi Lab - S10 FE + Windows 10
::  Motor auto-detectado: API key OU Claude Code CLI (plano Pro)
::  Duplo clique para iniciar tudo.
:: ================================================================

echo.
echo   ============================================================
echo    DataDev Demarchi Lab -- Detectando motor de processamento
echo   ============================================================
echo.

:: ---- Garantir npm no PATH (para claude CLI) ---------------------
set "NPM_BIN=%APPDATA%\npm"
if exist "%NPM_BIN%" (
    echo %PATH% | find /i "%NPM_BIN%" > nul
    if errorlevel 1 set "PATH=%NPM_BIN%;%PATH%"
)

:: ---- Tentar carregar API key do .env ----------------------------
set "ENV_FILE=%~dp0.env"
if exist "%ENV_FILE%" (
    for /f "usebackq eol=# tokens=1,* delims==" %%K in ("%ENV_FILE%") do (
        if /i "%%K"=="ANTHROPIC_API_KEY" set "ANTHROPIC_API_KEY=%%L"
    )
)

:: ---- Decidir motor: API key valida? -----------------------------
set "MOTOR=nenhum"

if defined ANTHROPIC_API_KEY (
    if not "%ANTHROPIC_API_KEY%"=="sk-ant-COLE-SUA-CHAVE-AQUI" (
        if not "%ANTHROPIC_API_KEY%"=="" (
            set "_M=%ANTHROPIC_API_KEY:~0,18%..."
            echo   [OK] Motor: API Anthropic  ^(%_M%^)
            set "MOTOR=api"
        )
    )
)

:: ---- Se nao tem API key: tentar Claude Code CLI -----------------
if "%MOTOR%"=="nenhum" (
    claude --version > nul 2>&1
    if not errorlevel 1 (
        :: CLI presente - verificar se esta autenticado
        for /f "delims=" %%R in ('claude -p "responda so: OK" 2^>^&1') do set "_CLI_TEST=%%R"
        echo %_CLI_TEST% | find /i "Not logged in" > nul
        if errorlevel 1 (
            echo %_CLI_TEST% | find /i "OK" > nul
            if not errorlevel 1 (
                echo   [OK] Motor: Claude Code CLI ^(plano Pro^) - autenticado
                set "MOTOR=claude_code"
            ) else (
                echo   [OK] Motor: Claude Code CLI ^(plano Pro^) - detectado
                set "MOTOR=claude_code"
            )
        ) else (
            echo   [!!] Claude Code CLI encontrado mas NAO autenticado
            echo        Execute CONECTAR-CLAUDE.bat primeiro
        )
    )
)

:: ---- Nenhum motor disponivel ------------------------------------
if "%MOTOR%"=="nenhum" (
    echo.
    echo   [XX] Nenhum motor de processamento disponivel.
    echo.
    echo   Opcao A - Claude Pro ^(sem custo extra^):
    echo     1. Execute CONECTAR-CLAUDE.bat
    echo     2. Digite /login no Claude Code que abrir
    echo     3. Execute este arquivo novamente
    echo.
    echo   Opcao B - API Anthropic:
    echo     1. Acesse https://console.anthropic.com/
    echo     2. Edite o arquivo .env com sua chave
    echo     3. Execute este arquivo novamente
    echo.
    pause
    exit /b 1
)

echo.

:: ---- Iniciar pipeline -------------------------------------------
:iniciar
powershell -ExecutionPolicy Bypass -File "%~dp0start-integracao.ps1"
pause
