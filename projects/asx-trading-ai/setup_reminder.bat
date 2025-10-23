@echo off
REM Setup Windows reminder for tomorrow at 10:00 AM

echo Setting up reminder for tomorrow at 10:00 AM...
echo.

schtasks /create /tn "ASX_Trading_Test_Reminder" /tr "%~dp0reminder_10am.vbs" /sc once /st 10:00 /sd 10/14/2025 /f

echo.
echo ========================================
echo Reminder set for tomorrow at 10:00 AM!
echo ========================================
echo.
echo A popup will remind you to start the test.
echo.
pause
