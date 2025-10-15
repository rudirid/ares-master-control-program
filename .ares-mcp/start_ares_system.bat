@echo off
echo ======================================================================
echo ARES SYSTEM LAUNCHER
echo ======================================================================
echo.
echo Starting complete Ares WhatsApp system...
echo.
echo [1/3] Starting WhatsApp Bridge...
start "Ares WhatsApp Bridge" python C:\Users\riord\.ares-mcp\whatsapp_bridge.py
timeout /t 2 /nobreak >nul

echo [2/3] Starting Message Poller (offline backup)...
start "Ares Message Poller" /MIN python C:\Users\riord\.ares-mcp\whatsapp_poller.py
timeout /t 2 /nobreak >nul

echo [3/3] Starting Ares Daemon...
start "Ares Daemon" python C:\Users\riord\.ares-mcp\ares_daemon.py
timeout /t 2 /nobreak >nul

echo.
echo ======================================================================
echo ARES SYSTEM RUNNING
echo ======================================================================
echo.
echo Three windows opened:
echo   1. Ares WhatsApp Bridge (port 5000)
echo   2. Ares Message Poller (background, minimized)
echo   3. Ares Daemon (auto-processor)
echo.
echo Benefits:
echo   - Messages queue even when windows are closed
echo   - Automatic message retrieval when internet reconnects
echo   - 24/7 message monitoring
echo.
echo Send a WhatsApp message to test!
echo.
echo To stop: Close all windows or press Ctrl+C
echo ======================================================================
pause
