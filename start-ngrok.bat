@echo off
REM Start Ngrok Tunnel for VANI (Windows Batch Script)
REM This is a simple wrapper for the PowerShell script

echo ========================================
echo   Starting Ngrok Tunnel for VANI
echo ========================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PowerShell not found!
    echo.
    echo Please install PowerShell or use ngrok directly:
    echo   ngrok http 5000 --domain=vani-dev.ngrok.app
    echo.
    pause
    exit /b 1
)

REM Check if ngrok is installed
where ngrok >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ngrok not found in PATH!
    echo.
    echo Please install ngrok:
    echo   1. Download from: https://ngrok.com/download
    echo   2. Extract to a folder in your PATH
    echo   3. Or install via: choco install ngrok
    echo   4. Configure authtoken: ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

echo [OK] Starting ngrok via PowerShell script...
echo.

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\start_ngrok.ps1" %*

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start ngrok
    echo.
    echo Alternative: Run ngrok manually:
    echo   ngrok http 5000 --domain=vani-dev.ngrok.app
    echo.
    pause
)








