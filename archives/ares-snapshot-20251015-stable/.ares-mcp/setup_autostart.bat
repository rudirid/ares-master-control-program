@echo off
REM Setup WhatsApp Bridge to auto-start on Windows login

echo ======================================================================
echo SETUP WHATSAPP BRIDGE AUTO-START
echo ======================================================================
echo.

echo This will create a scheduled task to start the WhatsApp bridge
echo automatically when you log in to Windows.
echo.
echo Task Name: AresWhatsAppBridge
echo Script: C:\Users\riord\.ares-mcp\auto_start_whatsapp.bat
echo.
pause

REM Delete existing task if it exists
schtasks /Delete /TN "AresWhatsAppBridge" /F 2>nul

REM Create new scheduled task
schtasks /Create /TN "AresWhatsAppBridge" /TR "C:\Users\riord\.ares-mcp\auto_start_whatsapp.bat" /SC ONLOGON /RL HIGHEST /F

if %errorlevel% == 0 (
    echo.
    echo ======================================================================
    echo SUCCESS - Auto-start configured
    echo ======================================================================
    echo.
    echo The WhatsApp bridge will now start automatically when you log in.
    echo.
    echo To manage the task:
    echo   - View: schtasks /Query /TN "AresWhatsAppBridge"
    echo   - Disable: schtasks /Change /TN "AresWhatsAppBridge" /DISABLE
    echo   - Enable: schtasks /Change /TN "AresWhatsAppBridge" /ENABLE
    echo   - Remove: schtasks /Delete /TN "AresWhatsAppBridge" /F
    echo.
    echo Starting the bridge now...
    start "" "C:\Users\riord\.ares-mcp\auto_start_whatsapp.bat"
) else (
    echo.
    echo ERROR - Failed to create scheduled task
    echo You may need to run this script as Administrator
)

echo.
pause
