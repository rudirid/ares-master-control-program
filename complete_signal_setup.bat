@echo off
REM Ares Complete Signal Setup - One-Command Installation
REM This script completes the entire Signal bridge setup after Java is installed

echo ========================================================================
echo ARES COMPLETE SIGNAL SETUP
echo ========================================================================
echo.
echo This script will:
echo   1. Check Java is installed
echo   2. Auto-download and install signal-cli
echo   3. Link your Signal account
echo   4. Test the connection
echo.

REM Step 1: Check Java
echo [STEP 1/4] Checking Java...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java not installed yet
    echo.
    echo Please install Java first from: https://adoptium.net
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)
echo [OK] Java is installed
echo.

REM Step 2: Install signal-cli using PowerShell script
echo [STEP 2/4] Installing signal-cli...
echo This will download signal-cli v0.13.5 from GitHub...
echo.
powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\.ares-mcp\install_signal_cli.ps1"
if %errorlevel% neq 0 (
    echo [ERROR] signal-cli installation failed
    pause
    exit /b 1
)
echo.

REM Step 3: Link Signal account
echo [STEP 3/4] Linking Signal account...
echo.
echo ========================================================================
echo IMPORTANT: Have your iPhone ready!
echo ========================================================================
echo.
echo In a moment, a QR code will appear.
echo.
echo On your iPhone:
echo   1. Open Signal app
echo   2. Tap your profile (top left)
echo   3. Settings -^> Linked Devices
echo   4. Tap "Link New Device"
echo   5. Scan the QR code that appears
echo.
pause

echo.
echo Starting Signal bridge (will prompt for phone number)...
python "%USERPROFILE%\.ares-mcp\signal_bridge.py"

REM If we get here, linking was successful
echo.
echo ========================================================================
echo SETUP COMPLETE!
echo ========================================================================
echo.
echo Signal bridge is now configured and running.
echo.
echo To use:
echo   1. Send a message from iPhone Signal (Note to Self)
echo   2. Ares will respond with: "Task received and queued"
echo   3. Run: python %USERPROFILE%\.ares-mcp\ares_task_processor.py
echo.
echo Commands you can send:
echo   - "status"  = Check task queue
echo   - "list"    = Show pending tasks
echo   - Any text  = Queue as task for Ares
echo.
echo ========================================================================
pause
