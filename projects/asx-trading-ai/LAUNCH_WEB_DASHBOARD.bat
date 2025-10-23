@echo off
title ASX Trading AI - Web Dashboard Launcher
echo.
echo ========================================
echo  ASX Trading AI - Web Dashboard
echo ========================================
echo.
echo Starting web server...
echo.

cd /d "%~dp0"

REM Start the Python server in the background
start /B python dashboard_server.py

REM Wait a few seconds for server to start
timeout /t 3 /nobreak >nul

REM Open the dashboard in default browser
start dashboard.html

echo.
echo ========================================
echo  Dashboard opened in your browser!
echo ========================================
echo.
echo Server is running at: http://localhost:8000
echo Dashboard auto-refreshes every 30 seconds
echo.
echo Press any key to stop the server and close...
pause >nul

REM Kill the Python server
taskkill /F /IM python.exe /FI "WINDOWTITLE eq dashboard_server.py*" >nul 2>&1

echo.
echo Server stopped.
