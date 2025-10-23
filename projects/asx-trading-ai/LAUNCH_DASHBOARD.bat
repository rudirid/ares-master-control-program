@echo off
title ASX Trading AI - Financial Dashboard
echo.
echo ========================================
echo  ASX Trading AI - Financial Dashboard
echo ========================================
echo.
echo Starting professional analysis interface...
echo.

cd /d "%~dp0"
python financial_dashboard.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start dashboard
    echo Please ensure Python and required packages are installed
    echo.
    pause
)
