@echo off
title DataDev Lab - Conectar Claude Code CLI
chcp 65001 > nul
powershell -ExecutionPolicy Bypass -File "%~dp0connect-claude.ps1"
