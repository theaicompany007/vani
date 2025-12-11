@echo off

echo ========================================
echo   VANI - Virtual Agent Network Interface
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo [1/2] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Check if dependencies are installed
echo [2/2] Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Start the app
echo Starting VANI application...
echo.
python run.py

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error
    pause
)
