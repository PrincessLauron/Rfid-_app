@echo off
setlocal EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: ── Virtual environment ──────────────────────────────────────────────────────
if not exist ".venv\" (
    echo [setup] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [error] Failed to create venv. Is Python 3.10+ installed?
        echo         Download from https://www.python.org/downloads/
        pause & exit /b 1
    )
)

call .venv\Scripts\activate.bat

:: ── Dependencies ─────────────────────────────────────────────────────────────
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [setup] Installing dependencies...
    pip install -r requirements-windows.txt
    if errorlevel 1 (
        echo [error] pip install failed.
        pause & exit /b 1
    )
)

:: ── Migrations ───────────────────────────────────────────────────────────────
echo [db] Running migrations...
alembic upgrade head
if errorlevel 1 (
    echo [error] Alembic migration failed.
    pause & exit /b 1
)

:: ── Seed ─────────────────────────────────────────────────────────────────────
echo [db] Seeding defaults...
python -m backend.app.seed

:: ── Start ────────────────────────────────────────────────────────────────────
echo.
echo [web] Starting app at http://127.0.0.1:8000
echo       Default login:  admin / admin123
echo       Press Ctrl+C to stop.
echo.
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
