@echo off
echo ======================================================================
echo ARES WHATSAPP BRIDGE LAUNCHER
echo ======================================================================
echo.

echo [1/3] Starting ngrok tunnel...
start "Ngrok Tunnel" cmd /c "cd C:\Users\riord && ngrok.exe http 5000"

echo Waiting 5 seconds for ngrok to start...
timeout /t 5 /nobreak > nul

echo.
echo [2/3] Getting ngrok URL...
curl -s http://localhost:4040/api/tunnels > ngrok_info.json
echo.

echo [3/3] Starting WhatsApp Bridge server...
echo.
echo ======================================================================
echo BRIDGE ACTIVE - Keep this window open
echo ======================================================================
echo.
echo To configure Meta webhook:
echo 1. Open: https://developers.facebook.com/apps
echo 2. Go to: WhatsApp -^> Configuration
echo 3. Get ngrok URL from ngrok window (https://xxxx.ngrok.io)
echo 4. Set Callback URL: https://xxxx.ngrok.io/webhook
echo 5. Set Verify Token: ares_webhook_verify_2024
echo.
echo ======================================================================
echo.

cd C:\Users\riord\.ares-mcp
python whatsapp_bridge.py

pause
