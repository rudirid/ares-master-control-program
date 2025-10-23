@echo off
REM Installation script for ASX Trading AI dependencies
REM Run this in Command Prompt or PowerShell

echo ===============================================================================
echo ASX Trading AI - Dependency Installation
echo ===============================================================================
echo.

cd /d "%~dp0"

echo [1/7] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/7] Installing core ML dependencies (this may take 5-10 minutes)...
pip install --upgrade transformers torch torchvision torchaudio

echo.
echo [3/7] Installing NLP dependencies...
pip install sentencepiece protobuf

echo.
echo [4/7] Installing scientific computing libraries...
pip install scipy numpy pandas scikit-learn

echo.
echo [5/7] Installing API and data handling libraries...
pip install ib_insync yfinance requests beautifulsoup4

echo.
echo [6/7] Installing monitoring and MLOps tools...
pip install mlflow prometheus-client

echo.
echo [7/7] Installing testing frameworks...
pip install pytest pytest-cov

echo.
echo ===============================================================================
echo Installation Complete!
echo ===============================================================================
echo.
echo Verifying installations...
python -c "import torch; import transformers; import yfinance; import pandas; print('All core packages installed successfully!')"

echo.
echo You can now run the trading system:
echo   - Live demo: python live_trading\enhanced_gui_demo.py
echo   - Live trading: python live_trading\live_paper_trader.py
echo.
pause
