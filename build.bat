@echo off
title Compilando Control Parental...
echo ============================================
echo   COMPILANDO CONTROL PARENTAL PARA WINDOWS
echo ============================================
echo.

echo [1/3] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Fallo al instalar dependencias.
    pause
    exit /b 1
)

echo.
echo [2/3] Compilando ejecutable...
pyinstaller build.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: Fallo la compilacion.
    pause
    exit /b 1
)

echo.
echo [3/3] Copiando config.json a dist\...
if exist config.json (
    copy config.json dist\config.json >nul
    echo config.json copiado.
) else (
    echo AVISO: No se encontro config.json. Crea uno en dist\ antes de ejecutar.
)

echo.
echo ============================================
echo   LISTO: dist\ControlParental.exe
echo ============================================
echo.
echo IMPORTANTE: Edita dist\config.json con tus
echo tokens antes de ejecutar el programa.
echo.
pause
