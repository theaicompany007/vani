@echo off
REM ============================================
REM VANI App - Windows Virtual Environment Setup
REM ============================================

echo [STEP 1] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [STEP 2] Removing old virtual environment if exists...
if exist "venv" (
    echo Removing old venv folder...
    rmdir /s /q venv
)

echo.
echo [STEP 3] Creating new virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo [STEP 4] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo [STEP 5] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo [ERROR] Failed to upgrade pip
    pause
    exit /b 1
)

echo.
echo [STEP 6] Installing psycopg2-binary (optional - for direct PostgreSQL connections)...
REM Try to install psycopg2-binary from a pre-built wheel
pip install psycopg2-binary --only-binary :all: 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install psycopg2-binary with pre-built wheel
    echo Trying alternative versions...
    pip install psycopg2-binary==2.9.9 --only-binary :all: 2>nul
    if %errorlevel% neq 0 (
        pip install psycopg2-binary==2.9.5 --only-binary :all: 2>nul
        if %errorlevel% neq 0 (
            echo [WARNING] psycopg2-binary installation failed - this is OK for Python 3.13
            echo [INFO] psycopg2-binary is optional - Supabase client works without it
            echo [INFO] Direct PostgreSQL migrations will be unavailable, but Supabase REST API works fine
            echo.
            echo OPTIONAL: To enable direct PostgreSQL connections:
            echo 1. Install Microsoft C++ Build Tools from:
            echo    https://visualstudio.microsoft.com/visual-cpp-build-tools/
            echo 2. Then run: pip install psycopg2-binary
            echo.
            set PSYCOPG2_SKIPPED=1
        ) else (
            echo [SUCCESS] psycopg2-binary installed successfully
        )
    ) else (
        echo [SUCCESS] psycopg2-binary installed successfully
    )
) else (
    echo [SUCCESS] psycopg2-binary installed successfully
)

echo.
echo [STEP 7] Installing all other dependencies...
REM Create a temporary requirements file without psycopg2-binary
type requirements.txt | findstr /v "psycopg2-binary" > requirements_temp.txt
pip install -r requirements_temp.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install some dependencies
    echo Please review the error messages above
    pause
    exit /b 1
)

REM Clean up
del requirements_temp.txt

echo.
echo [STEP 8] Verifying installation...
python -c "import flask; import supabase; import dotenv; print('[SUCCESS] Core packages installed')"
if %errorlevel% neq 0 (
    echo [ERROR] Verification failed
    pause
    exit /b 1
)

if defined PSYCOPG2_SKIPPED (
    echo.
    echo [INFO] Note: psycopg2-binary was skipped (optional dependency)
    echo [INFO] VANI will work fine using Supabase REST API
)

echo.
echo ============================================
echo [SUCCESS] Virtual environment setup complete!
echo ============================================
echo.
echo To activate the virtual environment:
echo   venv\Scripts\activate
echo.
echo To run VANI:
echo   python run.py
echo.
echo Or use the VANI.bat file for automated setup
echo ============================================
pause

