@echo off
setlocal enabledelayedexpansion

set "PROJECT=%~dp0"
set "BACKUP_DIR=%PROJECT%..\nfc-backups"
set "TIMESTAMP=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"

echo Protecao NFC - Backup manual
echo.
echo Origem: %PROJECT%roms\
echo Destino: %BACKUP_DIR%\roms_%TIMESTAMP%\
echo.

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

xcopy /E /I /H /Y "%PROJECT%roms\*" "%BACKUP_DIR%\roms_%TIMESTAMP%\"

echo.
echo Backup concluido.
echo Pasta: %BACKUP_DIR%\roms_%TIMESTAMP%\
pause
