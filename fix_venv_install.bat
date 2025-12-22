@echo off
REM Quick fix to install dependencies, skipping psycopg2-binary if it fails
REM This is safe because psycopg2-binary is only needed for direct PostgreSQL connections
REM Supabase client works fine without it

echo ============================================
echo VANI - Quick Dependency Fix
echo ============================================
echo.

if not exist "venv" (
    echo [ERROR] Virtual environment not found. Please run setup_venv_windows.bat first.
    pause
    exit /b 1
)

echo [1] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo [2] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo.
echo [3] Installing dependencies (skipping psycopg2-binary if it fails)...
REM Create temporary requirements without psycopg2-binary
type requirements.txt | findstr /v "psycopg2-binary" > requirements_temp.txt

echo Installing core dependencies...
pip install -r requirements_temp.txt

if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies may have failed to install
    echo Please review the error messages above
) else (
    echo [SUCCESS] Core dependencies installed successfully
)

REM Clean up
del requirements_temp.txt 2>nul

echo.
echo [4] Attempting to install psycopg2-binary (optional)...
pip install psycopg2-binary --only-binary :all: 2>nul
if %errorlevel% neq 0 (
    echo [INFO] psycopg2-binary skipped - this is OK for Python 3.13
    echo [INFO] VANI will work using Supabase REST API (no direct PostgreSQL needed)
) else (
    echo [SUCCESS] psycopg2-binary installed
)

echo.
echo [5] Verifying core packages...
python -c "import flask; import supabase; from dotenv import load_dotenv; print('[SUCCESS] Core packages verified')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Core package verification failed
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo ============================================
echo [SUCCESS] Dependencies installed!
echo ============================================
echo.
echo You can now run VANI with:
echo   python run.py
echo.
pause

