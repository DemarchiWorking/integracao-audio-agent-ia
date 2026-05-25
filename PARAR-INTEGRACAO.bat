@echo off
title DataDev Lab - Parando Integracao...
powershell -ExecutionPolicy Bypass -File "%~dp0stop-integracao.ps1"
pause
