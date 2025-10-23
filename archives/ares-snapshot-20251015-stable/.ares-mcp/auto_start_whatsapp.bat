@echo off
REM Auto-start WhatsApp Bridge with persistent restart
REM This script runs in the background and keeps the bridge alive

echo ======================================================================
echo ARES WHATSAPP BRIDGE - AUTO-START SERVICE
echo ======================================================================
echo Starting at %date% %time%
echo.

:START_NGROK
echo [NGROK] Starting tunnel on port 5000...
start "Ares-Ngrok" /MIN cmd /c "cd C:\Users\riord && ngrok.exe http 5000"
echo [NGROK] Waiting 8 seconds for tunnel to establish...
timeout /t 8 /nobreak > nul

:START_BRIDGE
echo [BRIDGE] Starting WhatsApp bridge server...
cd C:\Users\riord\.ares-mcp

REM Run bridge - if it crashes, restart it
:BRIDGE_LOOP
echo [BRIDGE] Starting at %time%...
python whatsapp_bridge.py
echo.
echo [WARNING] Bridge stopped at %time%
echo [RESTART] Restarting in 5 seconds...
timeout /t 5 /nobreak > nul
goto BRIDGE_LOOP
