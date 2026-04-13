@echo off
REM ============================================================
REM iniciar.bat — Inicia NCA Dashboard en Windows
REM ============================================================
REM USO:
REM   iniciar.bat           -> Dashboard financiero NCA (puerto 5000)
REM   iniciar.bat ventas    -> Dashboard de ventas (puerto 5001)
REM   iniciar.bat ambos     -> Ambos servidores
REM   iniciar.bat instalar  -> Instala dependencias primero
REM ============================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set MODO=%1
if "%MODO%"=="" set MODO=nca

echo.
echo ============================================================
echo   NCA DASHBOARD
echo ============================================================

REM ── Verificar Python ─────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python no encontrado.
    echo   Descarga Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

REM ── Crear directorios necesarios ─────────────────────────────
if not exist "uploads" mkdir uploads
if not exist "output" mkdir output
if not exist "logs" mkdir logs

REM ── Crear users.json si no existe ────────────────────────────
if not exist "users.json" (
    if exist "users.example.json" (
        copy users.example.json users.json >nul
        echo   users.json creado desde ejemplo
    ) else (
        echo   ERROR: users.json no encontrado
        pause
        exit /b 1
    )
)

REM ── Instalar dependencias ─────────────────────────────────────
if "%MODO%"=="instalar" (
    echo   Instalando dependencias...
    pip install -r requirements.txt -q
    echo   Listo. Ejecuta iniciar.bat de nuevo para iniciar.
    pause
    exit /b 0
)

REM ── Verificar dependencias ────────────────────────────────────
python -c "import flask, pandas, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo   Dependencias no instaladas. Instalando...
    pip install -r requirements.txt -q
    echo.
)

REM ── Dashboard de Ventas ───────────────────────────────────────
if "%MODO%"=="ventas" (
    echo   Dashboard Ventas: http://localhost:5001
    echo   CTRL+C para detener
    echo ============================================================
    echo.
    python -X utf8 servidor_ventas.py
    pause
    exit /b 0
)

REM ── Ambos servidores ─────────────────────────────────────────
if "%MODO%"=="ambos" (
    echo   Dashboard NCA:    http://localhost:5000
    echo   Dashboard Ventas: http://localhost:5001
    echo   Cierra las ventanas para detener
    echo ============================================================
    echo.
    start "NCA Dashboard" python -X utf8 servidor_nca.py
    start "Ventas Dashboard" python -X utf8 servidor_ventas.py
    echo   Servidores iniciados en ventanas separadas.
    pause
    exit /b 0
)

REM ── Dashboard NCA (default) ───────────────────────────────────
echo   Dashboard NCA:  http://localhost:5000
echo   CTRL+C para detener
echo ============================================================
echo.
python -X utf8 servidor_nca.py

pause
