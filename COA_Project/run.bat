@echo off
chcp 65001 >nul
title C.O.A — Council of Agents
color 0B

echo.
echo ==========================================================
echo    C.O.A — Council of Agents v3.0
echo    Quick Launcher
echo ==========================================================
echo.

REM === Step 1: Check Admin ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] ERROR: This script requires Administrator privileges
    echo [!] Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)
echo [✓] Running as Administrator

REM === Step 2: Check Python ===
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] ERROR: Python is not installed
    echo [!] Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [✓] Python is installed

REM === Step 3: Check Ollama ===
ollama --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] ERROR: Ollama is not installed
    echo [!] Download from: https://ollama.com/download/windows
    pause
    exit /b 1
)
echo [✓] Ollama is installed

REM === Step 4: Check Ollama is running ===
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Ollama is not running. Starting...
    start /B ollama serve
    timeout /t 5 /nobreak >nul
)
echo [✓] Ollama is running

REM === Step 5: Check model is available ===
ollama list | findstr "llama3.1" >nul
if %errorLevel% neq 0 (
    echo [!] Model llama3.1 not found
    echo [!] Downloading... ^(this may take 10-15 minutes^)
    ollama pull llama3.1
)
echo [✓] Model llama3.1 is available

REM === Step 6: Setup virtual environment ===
if not exist "venv\" (
    echo [...] Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo [✓] Virtual environment activated

REM === Step 7: Install requirements ===
if not exist "venv\.installed" (
    echo [...] Installing requirements ^(first time only^)...
    pip install -r requirements.txt --quiet
    type nul > venv\.installed
)
echo [✓] All dependencies installed

REM === Step 8: Run the program ===
echo.
echo ==========================================================
echo    Choose what to run:
echo ==========================================================
echo    [1] CLI         (Command Line)
echo    [2] GUI         (Graphical Interface)
echo    [3] API Server  (For Helpdesk Bot)
echo    [4] Run Tests
echo    [5] Dry Run     (Safe simulation)
echo    [Q] Quit
echo ==========================================================
echo.
set /p choice="Your choice: "

if "%choice%"=="1" (
    python main.py
) else if "%choice%"=="2" (
    python gui.py
) else if "%choice%"=="3" (
    python helpdesk_api.py
) else if "%choice%"=="4" (
    python -m pytest tests/ -v
) else if "%choice%"=="5" (
    python main.py --dry-run --html
) else if /i "%choice%"=="Q" (
    exit /b 0
) else (
    echo Invalid choice
)

echo.
pause
