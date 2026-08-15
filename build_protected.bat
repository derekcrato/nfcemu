@echo off
setlocal

set "PROJECT=%~dp0"
set "PYTHON=python"

echo.
echo ==========================================
echo   NFC Launcher - Protecao de ROMs
echo ==========================================
echo.

echo [1/2] Verificando integridade das ROMs...
"%PYTHON%" "%PROJECT%scripts\verify_roms.py"
if errorlevel 1 (
    echo.
    echo FALHA: ROMs corrompidas ou ausentes.
    echo Execute scripts\backup_roms.bat se precisar restaurar.
    pause
    exit /b 1
)

echo.
echo [2/2] Executando build do projeto...
call "%PROJECT%scripts\build_all.py" %*
if errorlevel 1 (
    echo.
    echo FALHA: Build com erro.
    pause
    exit /b 1
)

echo.
echo Concluido com sucesso.
pause
