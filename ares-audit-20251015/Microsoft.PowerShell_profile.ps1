# PowerShell Profile - Auto-launch Claude Code and ARES
# Created for automatic startup on terminal launch

# Function to launch ARES system
function Start-Ares {
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "ARES SYSTEM LAUNCHER" -ForegroundColor Cyan
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Starting complete Ares WhatsApp system..." -ForegroundColor Yellow
    Write-Host ""

    # Launch WhatsApp Bridge
    Write-Host "[1/3] Starting WhatsApp Bridge..." -ForegroundColor Green
    Start-Process -FilePath "python" -ArgumentList "C:\Users\riord\.ares-mcp\whatsapp_bridge.py" -WindowStyle Normal
    Start-Sleep -Seconds 2

    # Launch Message Poller (background service)
    Write-Host "[2/3] Starting Message Poller (offline backup)..." -ForegroundColor Green
    Start-Process -FilePath "python" -ArgumentList "C:\Users\riord\.ares-mcp\whatsapp_poller.py" -WindowStyle Minimized
    Start-Sleep -Seconds 2

    # Launch Ares Daemon
    Write-Host "[3/3] Starting Ares Daemon..." -ForegroundColor Green
    Start-Process -FilePath "python" -ArgumentList "C:\Users\riord\.ares-mcp\ares_daemon.py" -WindowStyle Normal
    Start-Sleep -Seconds 2

    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "ARES SYSTEM RUNNING" -ForegroundColor Cyan
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Three windows opened:" -ForegroundColor Yellow
    Write-Host "  1. Ares WhatsApp Bridge (port 5000)" -ForegroundColor White
    Write-Host "  2. Ares Message Poller (background, minimized)" -ForegroundColor White
    Write-Host "  3. Ares Daemon (auto-processor)" -ForegroundColor White
    Write-Host ""
    Write-Host "Benefits:" -ForegroundColor Green
    Write-Host "  - Messages queue even when windows are closed" -ForegroundColor White
    Write-Host "  - Automatic message retrieval when internet reconnects" -ForegroundColor White
    Write-Host "  - 24/7 message monitoring" -ForegroundColor White
    Write-Host ""
    Write-Host "Send a WhatsApp message to test!" -ForegroundColor Green
    Write-Host ""
}

# Function to auto-launch Claude Code
function Start-ClaudeCode {
    Write-Host "======================================================================" -ForegroundColor Magenta
    Write-Host "CLAUDE CODE LAUNCHER" -ForegroundColor Magenta
    Write-Host "======================================================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "Launching Claude Code in this window..." -ForegroundColor Yellow
    Write-Host ""
}

# Auto-start sequence
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "           AUTOMATIC STARTUP SEQUENCE INITIATED                         " -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Prompt user for automatic launch
$response = Read-Host "Launch Claude Code and ARES automatically? (Y/n)"

if (($response -eq "") -or ($response -match "^[Yy]"))
{
    Write-Host ""
    Write-Host "Starting automatic launch sequence..." -ForegroundColor Green
    Write-Host ""

    # Launch ARES first (in background windows)
    Start-Ares

    # Show Claude Code banner
    Start-ClaudeCode

    # Execute Claude Code in THIS window (will take over the terminal)
    & claude code
}
else
{
    Write-Host ""
    Write-Host "Automatic launch cancelled. You can manually start systems with:" -ForegroundColor Yellow
    Write-Host "  - Start-ClaudeCode  (to launch Claude Code)" -ForegroundColor White
    Write-Host "  - Start-Ares        (to launch ARES)" -ForegroundColor White
    Write-Host ""
}

# Set working directory to home
Set-Location $HOME

# Optional: Add custom prompt
function prompt {
    $path = Get-Location
    Write-Host "PS " -NoNewline -ForegroundColor Green
    Write-Host "$path" -NoNewline -ForegroundColor Cyan
    return "> "
}
