@echo off
title Instalando Control Parental...

:: Verificar que se ejecuta como administrador
net session >nul 2>&1
if errorlevel 1 (
    echo ERROR: Ejecuta este archivo como Administrador.
    echo Clic derecho sobre instalar.bat ^> Ejecutar como administrador
    pause
    exit /b 1
)

echo ============================================
echo   INSTALANDO CONTROL PARENTAL
echo ============================================
echo.

:: Directorio de instalacion
set "INSTALL_DIR=C:\Program Files\ControlParental"
set "EXE_SRC=%~dp0dist\ControlParental.exe"
set "CFG_SRC=%~dp0dist\config.json"

:: Verificar que el exe existe
if not exist "%EXE_SRC%" (
    echo ERROR: No se encontro ControlParental.exe
    echo Ejecuta build.bat primero.
    pause
    exit /b 1
)

:: Verificar que config.json tiene tokens reales
findstr /c:"TU_TOKEN_AQUI" "%CFG_SRC%" >nul 2>&1
if not errorlevel 1 (
    echo ERROR: config.json todavia tiene valores de ejemplo.
    echo Edita dist\config.json con tus tokens reales antes de instalar.
    pause
    exit /b 1
)

echo [1/3] Copiando archivos a %INSTALL_DIR%...
mkdir "%INSTALL_DIR%" 2>nul
copy "%EXE_SRC%" "%INSTALL_DIR%\ControlParental.exe" >nul
copy "%CFG_SRC%" "%INSTALL_DIR%\config.json" >nul

echo [2/3] Configurando inicio automatico con Windows...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" ^
    /v "ControlParental" ^
    /t REG_SZ ^
    /d "\"%INSTALL_DIR%\ControlParental.exe\"" ^
    /f >nul

echo [3/3] Iniciando el programa...
start "" "%INSTALL_DIR%\ControlParental.exe"

echo.
echo ============================================
echo   INSTALACION COMPLETA
echo ============================================
echo.
echo El sistema arrancara automaticamente con Windows.
echo Ejecutable: %INSTALL_DIR%\ControlParental.exe
echo.
pause
