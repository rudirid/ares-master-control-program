@echo off
echo ======================================================================
echo ARES SYSTEM LAUNCHER
echo ======================================================================
echo.
echo Starting complete Ares WhatsApp system...
echo.
echo [1/2] Starting WhatsApp Bridge...
start "Ares WhatsApp Bridge" python C:\Users\riord\.ares-mcp\whatsapp_bridge.py
timeout /t 3 /nobreak >nul

echo [2/2] Starting Ares Daemon...
start "Ares Daemon" python C:\Users\riord\.ares-mcp\ares_daemon.py
timeout /t 2 /nobreak >nul

echo.
echo ======================================================================
echo ARES SYSTEM RUNNING
echo ======================================================================
echo.
echo Two windows opened:
echo   1. Ares WhatsApp Bridge (port 5000)
echo   2. Ares Daemon (auto-processor)
echo.
echo Send a WhatsApp message to test!
echo.
echo To stop: Close both windows or press Ctrl+C
echo ======================================================================
pause
