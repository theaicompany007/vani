@echo off
echo Building Tailwind CSS...
echo.

REM Check if node is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if npm is installed
where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if node_modules exists, if not install dependencies
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Build CSS
echo Building CSS...
call npm run build-css

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: Tailwind CSS built successfully!
    echo Output: app\static\css\tailwind.css
) else (
    echo.
    echo ERROR: Failed to build CSS
    pause
    exit /b 1
)

pause

















