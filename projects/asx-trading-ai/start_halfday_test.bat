@echo off
REM Half-Day Live Trading Test
REM Run this tomorrow at 10:00 AM
REM Press Ctrl+C at 2:30 PM to stop

echo ========================================
echo ASX TRADING AI - HALF-DAY TEST
echo ========================================
echo.
echo Start Time: %TIME%
echo Press Ctrl+C at 2:30 PM to stop
echo.
echo ========================================
echo.

cd /d "%~dp0"

REM Clear old test data
echo Clearing old test data...
sqlite3 stock_data.db "DELETE FROM live_announcements WHERE 1=1;"
sqlite3 stock_data.db "DELETE FROM live_recommendations WHERE 1=1;"
echo.

REM Show current stats (should be 0)
echo Current stats:
python live_trading/check_stats.py --summary
echo.

REM Start live collection
echo Starting live collection...
echo Monitoring ASX announcements every 10 seconds
echo.
python live_trading/live_paper_trader.py --duration-days 1 --interval 10

pause
