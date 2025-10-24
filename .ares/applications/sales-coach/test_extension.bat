@echo off
REM Quick test script for Sales Coach Extension

echo ================================================================================
echo SALES COACH EXTENSION - QUICK TEST
echo ================================================================================
echo.

REM Check if icons exist
if not exist "extension\icons\icon16.png" (
    echo [1/3] Creating placeholder icons...
    cd extension
    python create_placeholder_icons.py
    cd ..
    echo      Icons created!
) else (
    echo [1/3] Icons already exist
)

echo.
echo [2/3] Starting backend server...
echo      Server will run on http://localhost:5001
echo      Keep this window open during testing
echo.
echo [3/3] Next steps:
echo      1. Open Chrome
echo      2. Go to chrome://extensions/
echo      3. Enable Developer mode
echo      4. Click "Load unpacked"
echo      5. Select: %CD%\extension
echo      6. Join Google Meet
echo      7. Click extension icon and "Start Coaching"
echo.
echo ================================================================================
echo STARTING SERVER... (Press Ctrl+C to stop)
echo ================================================================================
echo.

python extension_server.py
