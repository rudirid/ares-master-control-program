@echo off
REM Ares Signal Bridge - Windows Setup Script
REM This script helps you set up Signal integration on Windows

echo ========================================================================
echo ARES SIGNAL BRIDGE - Windows Setup
echo ========================================================================
echo.

REM Check if Java is installed
echo [1/4] Checking Java installation...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java is not installed
    echo.
    echo Please install Java:
    echo 1. Go to: https://adoptium.net
    echo 2. Download "Temurin 17 LTS" for Windows
    echo 3. Run installer with default settings
    echo 4. Restart this script after installation
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Java is installed
)

echo.
echo [2/4] Checking signal-cli installation...
where signal-cli >nul 2>&1
if %errorlevel% neq 0 (
    if exist "C:\signal-cli\bin\signal-cli.bat" (
        echo [OK] signal-cli found at C:\signal-cli
        set SIGNAL_CLI=C:\signal-cli\bin\signal-cli.bat
    ) else (
        echo [ERROR] signal-cli is not installed
        echo.
        echo Please install signal-cli:
        echo 1. Go to: https://github.com/AsamK/signal-cli/releases
        echo 2. Download latest "signal-cli-[version]-Windows.zip"
        echo 3. Extract to C:\signal-cli
        echo 4. Restart this script after extraction
        echo.
        pause
        exit /b 1
    )
) else (
    echo [OK] signal-cli found in PATH
    set SIGNAL_CLI=signal-cli
)

echo.
echo [3/4] Checking Signal account linking...
if not exist "%USERPROFILE%\.ares-mcp\signal_config.json" (
    echo [INFO] Signal account not linked yet
    echo.
    echo Please have your phone ready!
    echo.
    echo Next steps:
    echo 1. You'll see a QR code appear
    echo 2. Open Signal on your iPhone
    echo 3. Go to: Settings -^> Linked Devices -^> Link New Device
    echo 4. Scan the QR code with your iPhone
    echo.
    pause

    echo.
    echo Starting linking process...
    python "%USERPROFILE%\.ares-mcp\signal_bridge.py"
) else (
    echo [OK] Signal account already linked
)

echo.
echo [4/4] Setup complete!
echo.
echo ========================================================================
echo HOW TO USE:
echo ========================================================================
echo.
echo Start the Signal bridge:
echo   python %USERPROFILE%\.ares-mcp\signal_bridge.py
echo.
echo Send test message from iPhone Signal:
echo   - Open Signal app
echo   - Go to "Note to Self"
echo   - Send: "Test connection"
echo.
echo Process queued tasks:
echo   python %USERPROFILE%\.ares-mcp\ares_task_processor.py
echo.
echo ========================================================================
pause
