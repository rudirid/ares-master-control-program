# Ares Signal-CLI Auto-Installer for Windows
# Downloads and installs signal-cli automatically

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "ARES SIGNAL-CLI AUTO-INSTALLER" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$signalCliVersion = "0.13.5"
$downloadUrl = "https://github.com/AsamK/signal-cli/releases/download/v$signalCliVersion/signal-cli-$signalCliVersion-Windows.zip"
$installPath = "C:\signal-cli"
$zipFile = "$env:TEMP\signal-cli.zip"

Write-Host "[1/4] Checking Java installation..." -ForegroundColor Yellow
try {
    $javaVersion = java -version 2>&1 | Select-String "version"
    Write-Host "[OK] Java is installed: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Java not found. Please install Java first:" -ForegroundColor Red
    Write-Host "  https://adoptium.net" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/4] Downloading signal-cli v$signalCliVersion..." -ForegroundColor Yellow
Write-Host "  From: $downloadUrl" -ForegroundColor Gray

try {
    # Download with progress
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFile -UseBasicParsing
    Write-Host "[OK] Downloaded: $zipFile" -ForegroundColor Green

    # Check file size
    $fileSize = (Get-Item $zipFile).Length / 1MB
    Write-Host "  Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Download failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/4] Installing to $installPath..." -ForegroundColor Yellow

# Remove old installation if exists
if (Test-Path $installPath) {
    Write-Host "  Removing old installation..." -ForegroundColor Gray
    Remove-Item -Path $installPath -Recurse -Force
}

# Create install directory
New-Item -ItemType Directory -Path $installPath -Force | Out-Null

# Extract ZIP
try {
    Write-Host "  Extracting files..." -ForegroundColor Gray
    Expand-Archive -Path $zipFile -DestinationPath $installPath -Force

    # Move contents up one level (signal-cli extracts to a subfolder)
    $extractedFolder = Get-ChildItem -Path $installPath -Directory | Select-Object -First 1
    if ($extractedFolder) {
        $items = Get-ChildItem -Path $extractedFolder.FullName
        foreach ($item in $items) {
            Move-Item -Path $item.FullName -Destination $installPath -Force
        }
        Remove-Item -Path $extractedFolder.FullName -Recurse -Force
    }

    Write-Host "[OK] Extracted to: $installPath" -ForegroundColor Green

    # Clean up ZIP
    Remove-Item $zipFile -Force
} catch {
    Write-Host "[ERROR] Extraction failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/4] Adding to system PATH..." -ForegroundColor Yellow

# Add to PATH if not already there
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$signalCliBin = "$installPath\bin"

if ($currentPath -notlike "*$signalCliBin*") {
    try {
        $newPath = "$currentPath;$signalCliBin"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "[OK] Added to PATH: $signalCliBin" -ForegroundColor Green
        Write-Host "  Note: You may need to restart your terminal" -ForegroundColor Gray
    } catch {
        Write-Host "[WARNING] Could not add to PATH automatically" -ForegroundColor Yellow
        Write-Host "  You can run signal-cli using full path:" -ForegroundColor Yellow
        Write-Host "  $signalCliBin\signal-cli.bat" -ForegroundColor Gray
    }
} else {
    Write-Host "[OK] Already in PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Test installation
Write-Host "Testing signal-cli..." -ForegroundColor Yellow
try {
    $testResult = & "$signalCliBin\signal-cli.bat" --version 2>&1
    Write-Host "[OK] signal-cli version: $testResult" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Test failed, but installation may still work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Close and reopen your terminal (for PATH to update)" -ForegroundColor White
Write-Host "2. Link your Signal account:" -ForegroundColor White
Write-Host "   python C:\Users\riord\.ares-mcp\signal_bridge.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Or run the full path if PATH not working:" -ForegroundColor White
Write-Host "   $signalCliBin\signal-cli.bat --version" -ForegroundColor Gray
Write-Host ""
