# Quick Fix: Signal Bridge Not Responding

## Problem
You sent "Test1. Confirm signal ares connection live" from iPhone Signal but got no response.

## Root Cause
Signal bridge requires 3 things that aren't installed yet:
1. Java (signal-cli needs it)
2. signal-cli (receives Signal messages)
3. Linked Signal account (connects your phone)

## Quick Fix (15 minutes)

### Step 1: Install Java
1. Open browser: https://adoptium.net
2. Download "Temurin 17 LTS" for Windows (x64)
3. Run installer → Click "Next" through everything
4. Close and reopen terminal after install

**Verify:**
```bash
java -version
# Should show: openjdk version "17.0.x"
```

### Step 2: Install signal-cli
1. Go to: https://github.com/AsamK/signal-cli/releases
2. Download latest `signal-cli-X.XX.X-Windows.zip`
3. Extract to `C:\signal-cli` (create this folder)
4. Your folder should look like:
   ```
   C:\signal-cli\
   ├── bin\
   │   └── signal-cli.bat
   └── lib\
   ```

**Verify:**
```bash
C:\signal-cli\bin\signal-cli.bat --version
# Should show: signal-cli 0.12.x
```

### Step 3: Link Your iPhone Signal Account
```bash
python C:\Users\riord\.ares-mcp\signal_bridge.py
```

**What happens:**
1. Script asks for your phone number
2. Enter format: `+12345678901` (+ country code, no spaces)
3. QR code appears in terminal
4. On iPhone:
   - Open Signal app
   - Tap profile icon (top left)
   - Settings → Linked Devices
   - Tap "Link New Device"
   - Scan QR code from terminal
5. Terminal shows: `[OK] Successfully linked!`

### Step 4: Start Signal Bridge
```bash
python C:\Users\riord\.ares-mcp\signal_bridge.py
```

**You'll see:**
```
[ARES SIGNAL BRIDGE] Starting...
[INFO] Phone: +12345678901
[OK] Listening for messages...
```

### Step 5: Test from iPhone
1. Open Signal app
2. Go to "Note to Self" (or send to yourself)
3. Send: `Hello Ares`
4. You should get instant reply:
   ```
   🎯 Ares here. Task #1 received and queued.

   I'll process this when your terminal comes online.

   Commands: 'status', 'list'
   ```

## If You Get Stuck

**Java won't install:**
- Make sure you downloaded the Windows x64 version
- Run installer as Administrator (right-click → Run as administrator)

**signal-cli won't run:**
- Check it's extracted to exactly `C:\signal-cli`
- Try full path: `C:\signal-cli\bin\signal-cli.bat --version`

**QR code won't scan:**
- Make terminal window fullscreen
- Try increasing terminal font size
- Make sure iPhone camera has permission

**Still no response from Ares:**
- Check signal_bridge.py is still running (don't close terminal)
- Verify phone number format: `+12345678901` (no spaces, no dashes)
- Check you're sending to "Note to Self" in Signal

## Automated Setup (Alternative)

Run this instead to get step-by-step guidance:
```bash
C:\Users\riord\.ares-mcp\setup_signal_windows.bat
```

This script checks each requirement and tells you exactly what's missing.

## Your Test Message

Your message "Test1. Confirm signal ares connection live" is waiting in Signal. Once you complete setup above, send a new test message and Ares will respond immediately!

---

**Time estimate:** 15 minutes (most time is downloading Java/signal-cli)
