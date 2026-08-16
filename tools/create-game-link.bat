@echo off
chcp 65001 >nul
title NFC Game Link Creator
color 0a

echo.
echo ========================================
echo    NFC Game Link Creator
echo ========================================
echo.

set /p url="Cole a URL do jogo do retrogames.cc: "

if "%url%"=="" (
    echo.
    echo [ERRO] URL nao pode estar vazia!
    pause
    exit /b 1
)

echo.
echo [1/3] Buscando informacoes do jogo...

cd /d "%~dp0"
node create-game-link.js "%url%"

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao criar o link!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Pronto! Link NFC criado com sucesso!
echo ========================================
echo.
echo Agora voce pode gravar a URL em uma tag NFC.
echo.
pause
