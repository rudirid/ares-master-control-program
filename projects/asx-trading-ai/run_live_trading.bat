@echo off
echo ================================================================================
echo LIVE TRADING SYSTEM - Full Pipeline
echo ================================================================================
echo.
echo This will run for 48 hours (2 days) and execute:
echo   1. Monitor ASX announcements (every 10 seconds)
echo   2. Auto-generate recommendations (DEMO MODE for testing)
echo   3. Create trades automatically
echo   4. Update P&L every 60 seconds with real prices
echo   5. Auto-close trades based on exit rules
echo.
echo Dashboard: http://localhost:8000
echo Dashboard HTML: file:///C:\Users\riord\asx-trading-ai\dashboard.html
echo.
echo Press Ctrl+C to stop
echo ================================================================================
echo.

cd C:\Users\riord\asx-trading-ai

REM Start dashboard server in background
start /B python dashboard_server.py

REM Wait 2 seconds
timeout /t 2 /nobreak > nul

REM Run full live system
python live_full_system.py
