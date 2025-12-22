@echo off
REM ============================================================
REM PROJECT VANI - Virtual Agent Network Interface
REM Launcher Script - Activates venv and starts application
REM ============================================================

echo.
echo ============================================================
echo PROJECT VANI - Virtual Agent Network Interface
echo ============================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM [1/5] Check if venv exists, create if not
echo [1/5] Checking virtual environment...
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

REM [2/5] Activate virtual environment
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo   OK: Virtual environment activated

REM [3/5] Upgrade pip
echo [3/5] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo   WARNING: pip upgrade failed, continuing...
)

REM [4/5] Install/check dependencies
echo [4/5] Installing dependencies...
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

REM [5/5] Start the application
echo [5/5] Starting VANI application...
echo.
echo ============================================================
echo Starting Flask server...
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
echo Application stopped
echo ============================================================
pause
