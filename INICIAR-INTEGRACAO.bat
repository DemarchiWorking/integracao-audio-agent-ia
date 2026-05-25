@echo off
title DataDev Lab - Iniciando Integracao...
chcp 65001 > nul

:: ================================================================
::  INICIAR-INTEGRACAO.bat  v2.0
::  DataDev Demarchi Lab - S10 FE + Windows 10
::  Le ANTHROPIC_API_KEY do .env automaticamente antes de iniciar.
::  Duplo clique para iniciar tudo.
:: ================================================================

echo.
echo   ============================================================
echo    DataDev Demarchi Lab -- Carregando configuracao
echo   ============================================================
echo.

:: ---- Tentar carregar do .env ------------------------------------
set "ENV_FILE=%~dp0.env"

if exist "%ENV_FILE%" (
    :: Ler linhas no formato KEY=VALUE, ignorar # e linhas vazias
    for /f "usebackq eol=# tokens=1,* delims==" %%K in ("%ENV_FILE%") do (
        if /i "%%K"=="ANTHROPIC_API_KEY" set "ANTHROPIC_API_KEY=%%L"
    )
)

:: ---- Checar se a key foi carregada e e valida -------------------
if not defined ANTHROPIC_API_KEY goto :sem_key
if "%ANTHROPIC_API_KEY%"=="sk-ant-COLE-SUA-CHAVE-AQUI" goto :placeholder

:: Key valida encontrada
set "_M=%ANTHROPIC_API_KEY:~0,18%..."
echo   [OK] ANTHROPIC_API_KEY: %_M%
echo   [OK] Modo: AUTO-EXECUTE Claude ativado
echo.
goto :iniciar

:sem_key
if not exist "%ENV_FILE%" (
    echo   [!!] Arquivo .env nao encontrado
    echo        Crie: %ENV_FILE%
    echo        Conteudo: ANTHROPIC_API_KEY=sk-ant-SUA-CHAVE
) else (
    echo   [!!] ANTHROPIC_API_KEY nao encontrada no .env
)
echo.
echo   Claude processara audio mas NAO executara tarefas automaticamente.
echo   Consulte: https://console.anthropic.com/ para obter sua chave
echo.
goto :iniciar

:placeholder
echo   [!!] .env encontrado mas chave NAO foi configurada ainda.
echo.
echo   Edite o arquivo .env e cole sua chave real:
echo   %ENV_FILE%
echo.
echo   Pressione qualquer tecla para abrir o .env no Notepad...
pause > nul
notepad "%ENV_FILE%"
echo.
echo   Salve o arquivo e execute novamente.
pause
exit /b 1

:iniciar
:: ANTHROPIC_API_KEY e herdada automaticamente pelo PowerShell
powershell -ExecutionPolicy Bypass -File "%~dp0start-integracao.ps1"
pause
