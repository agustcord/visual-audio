@echo off
setlocal

:: ============================================================================
:: Lanzador del Visualizador de Audio para Drift (MVP)
:: Anclaje al directorio del script y soporte estricto de rutas con espacios
:: ============================================================================
set "SCRIPT_DIR=%~dp0"
set "PYTHONPATH=%SCRIPT_DIR%tools;%PYTHONPATH%"

:: ----------------------------------------------------------------------------
:: Diagnostico 1: Deteccion de Python (pythonw.exe, python.exe o py.exe)
:: ----------------------------------------------------------------------------
set "PYTHONW_BIN="
set "PYTHON_BIN="

where pythonw.exe >nul 2>nul
if not errorlevel 1 set "PYTHONW_BIN=pythonw.exe"

where python.exe >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_BIN=python.exe"
) else (
    where py.exe >nul 2>nul
    if not errorlevel 1 set "PYTHON_BIN=py.exe"
)

if "%PYTHONW_BIN%"=="" if "%PYTHON_BIN%"=="" (
    echo.
    echo ============================================================================
    echo ERROR: No se encontro Python en el sistema.
    echo ============================================================================
    echo El visualizador de audio requiere Python 3.10 o superior para funcionar.
    echo.
    echo Pasos para solucionarlo:
    echo  1. Descarga e instala Python desde https://www.python.org/downloads/
    echo  2. Asegurate de marcar la casilla "Add Python to PATH" durante la instalacion.
    echo ============================================================================
    echo.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------------------
:: Diagnostico 2: Deteccion de FFmpeg
:: ----------------------------------------------------------------------------
where ffmpeg.exe >nul 2>nul
if errorlevel 1 (
    echo.
    echo ============================================================================
    echo ERROR: No se encontro FFmpeg en el sistema [ffmpeg.exe no esta en el PATH].
    echo ============================================================================
    echo El visualizador utiliza FFmpeg para decodificar audio y codificar los
    echo videos WebM transparentes o en negro para Drift.
    echo.
    echo Pasos para solucionarlo:
    echo  1. Descarga FFmpeg [ej. desde https://ffmpeg.org/download.html o gyan.dev]
    echo  2. Agrega la carpeta 'bin' que contiene ffmpeg.exe a la variable PATH de Windows.
    echo ============================================================================
    echo.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------------------
:: Ejecucion: Despacho segun modo interactivo (GUI) o linea de comandos (CLI)
:: ----------------------------------------------------------------------------
cd /d "%SCRIPT_DIR%"

if "%~1"=="" (
    :: Modo interactivo (doble clic): Si pythonw esta disponible, lanza sin consola negra
    if defined PYTHONW_BIN (
        start "" "%PYTHONW_BIN%" -m visualizador.cli
        exit /b 0
    ) else (
        "%PYTHON_BIN%" -m visualizador.cli
        exit /b %ERRORLEVEL%
    )
) else (
    :: Modo linea de comandos: Ejecuta en la consola actual de forma sincrona
    if defined PYTHON_BIN (
        "%PYTHON_BIN%" -m visualizador.cli %*
        exit /b %ERRORLEVEL%
    ) else (
        "%PYTHONW_BIN%" -m visualizador.cli %*
        exit /b %ERRORLEVEL%
    )
)
