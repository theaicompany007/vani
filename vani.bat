@echo off
REM ============================================================
REM PROJECT VANI - Virtual Agent Network Interface
REM Launcher Script - Starts Redis + Flask App
REM ============================================================

echo.
echo ============================================================
echo PROJECT VANI - Virtual Agent Network Interface
echo ============================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM [0/6] NEW: Check/Start Redis via WSL  
echo [0/6] Checking Redis (WSL)...
wsl -d Ubuntu -e bash -c "redis-cli ping" >nul 2>&1
if errorlevel 1 (
    echo   Starting Redis in WSL...
    wsl -d Ubuntu -e bash -c "sudo service redis-server start" >nul 2>&1
    timeout /t 3 /nobreak >nul
    wsl -d Ubuntu -e bash -c "redis-cli ping" && echo   OK: Redis ready ^(PONG^) || echo   WARNING: Redis may not be ready
) else (
    echo   OK: Redis already running ^(PONG^)
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM [1/6] Check if venv exists, create if not
echo [1/6] Checking virtual environment...
if not exist "venv\" (
    echo   Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo   OK: Virtual environment created
) else (
    echo   OK: Virtual environment exists
)

REM [2/6] Activate virtual environment
echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo   OK: Virtual environment activated

REM [3/6] Upgrade pip
echo [3/6] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo   WARNING: pip upgrade failed, continuing...
)

REM [4/6] Install/check dependencies
echo [4/6] Installing dependencies...
if exist "requirements.txt" (
    python -m pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo   WARNING: Some dependencies may have failed to install
    ) else (
        echo   OK: Dependencies installed
    )
) else (
    echo   WARNING: requirements.txt not found
)

REM [5/6] Final Redis check before Flask
echo [5/6] Final Redis health check...
wsl redis-cli ping && echo   OK: Redis confirmed ready || echo   WARNING: Redis not responding - Flask may fail

REM [6/6] Start the application
echo [6/6] Starting VANI Flask application...
echo.
echo ============================================================
echo Flask server starting... ^(Redis: wsl redis-cli ping^)
echo Redis logs: wsl -d Ubuntu sudo service redis-server status
echo ============================================================
echo.

REM Run the application
python run.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Application exited with error code %errorlevel%
    echo ============================================================
    echo.
    pause
    exit /b %errorlevel%
)

REM If we get here, application exited normally
echo.
echo ============================================================
echo Application stopped ^(Redis still running^)
echo Stop Redis: wsl -d Ubuntu sudo service redis-server stop
echo ============================================================
pause
