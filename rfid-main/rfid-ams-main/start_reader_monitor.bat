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
python -c "import fastapi, serial" >nul 2>&1
if errorlevel 1 (
    echo [setup] Installing dependencies...
    pip install -r requirements-windows.txt
    if errorlevel 1 (
        echo [error] pip install failed.
        pause & exit /b 1
    )
)

:: ── CH340 driver reminder ────────────────────────────────────────────────────
echo.
echo [reader] CH340 driver required for USB-serial adapter.
echo          If the reader does not appear in the port list, download the driver:
echo          https://www.wch-ic.com/downloads/CH341SER_EXE.html
echo.

:: ── Start ────────────────────────────────────────────────────────────────────
echo [reader] Starting reader monitor at http://127.0.0.1:8010
echo          Open that URL in your browser.
echo          Press Ctrl+C to stop.
echo.
uvicorn reader_standalone.main:app --host 127.0.0.1 --port 8010
