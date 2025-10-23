# Resume Signal Setup After Terminal Restart

## Current Status
✅ Java (Temurin 17) installed
⏳ Terminal restart required for Java PATH to take effect
📋 Next: Run automated signal-cli installer

## When You Reopen Terminal

Run this ONE command:

```bash
C:\Users\riord\.ares-mcp\complete_signal_setup.bat
```

This will:
1. Verify Java is working
2. Auto-download signal-cli v0.13.5
3. Install to C:\signal-cli
4. Link your iPhone Signal account (QR code scanning)
5. Test the connection

## Have Your iPhone Ready

When the script asks, you'll need to:
1. Open Signal app on iPhone
2. Tap profile icon (top left)
3. Settings → Linked Devices
4. Tap "Link New Device"
5. Scan QR code from terminal

## If Java Test Fails

Try manually:
```bash
java -version
# Should show: openjdk version "17.0.x"
```

If not found, you may need to restart Windows completely (not just terminal).

## After Setup Completes

Send test message from iPhone Signal:
- Go to "Note to Self"
- Send: "Hello Ares"
- You should get instant reply

## Files Location

All automation scripts are in:
- `C:\Users\riord\.ares-mcp\complete_signal_setup.bat` (main setup)
- `C:\Users\riord\.ares-mcp\install_signal_cli.ps1` (installer)
- `C:\Users\riord\.ares-mcp\signal_bridge.py` (bridge)

## GitHub Backup

Everything pushed to:
https://github.com/rudirid/ares-master-control-program

---

**Next command to run after restart:**
```bash
C:\Users\riord\.ares-mcp\complete_signal_setup.bat
```
