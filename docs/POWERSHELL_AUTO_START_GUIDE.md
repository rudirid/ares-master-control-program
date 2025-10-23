# PowerShell Auto-Start Guide for Claude Code & ARES

## What Was Set Up

Your PowerShell terminal is now configured to automatically offer to launch:
1. **Claude Code** - Your AI coding assistant
2. **ARES** - Your WhatsApp automation system

## How It Works

When you open a new PowerShell terminal, you'll see:

```
========================================================================
           AUTOMATIC STARTUP SEQUENCE INITIATED
========================================================================

Launch Claude Code and ARES automatically? (Y/n)
```

- Press **Y** or **Enter** to launch both systems automatically
- Press **N** to skip automatic launch

## Profile Location

Your PowerShell profile is located at:
```
C:\Users\riord\OneDrive\_Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
```

## Manual Controls

If you choose not to auto-launch, you can manually start systems anytime:

- **Start-ClaudeCode** - Launch Claude Code
- **Start-Ares** - Launch ARES system

## What Happens on Auto-Launch

### 1. Claude Code Launch
- Runs `claude code` command
- Starts in current directory
- Opens in the same terminal window

### 2. ARES Launch
- Opens 2 separate windows:
  - **WhatsApp Bridge** (port 5000) - Receives WhatsApp messages
  - **Ares Daemon** - Processes tasks automatically
- Both run in background windows
- You can close them anytime with Ctrl+C

## Testing the Setup

To test without auto-launching everything:

```powershell
# Test in a new PowerShell window (responds "n" to prompt)
powershell

# Or test manually:
Start-ClaudeCode
Start-Ares
```

## Customization

To modify the auto-start behavior, edit the profile:

```powershell
notepad $PROFILE
```

Common customizations:
- Change default response from "Y" to auto-launch without prompting
- Adjust sleep timers between launches
- Modify launch order
- Add/remove systems from startup

## Disabling Auto-Start

### Temporary (one session):
```powershell
powershell -NoProfile
```

### Permanent:
1. Edit profile: `notepad $PROFILE`
2. Comment out or remove the auto-start section (lines 56-94)

## Troubleshooting

### Claude Code doesn't launch
- Ensure `claude` command is in your PATH
- Try running `claude --version` to verify installation
- Update the profile to use full path to claude executable

### ARES doesn't launch
- Ensure Python is installed and in PATH
- Verify ARES files exist at: `C:\Users\riord\.ares-mcp\`
- Check that WhatsApp bridge setup is complete

### Profile errors on startup
- Run: `powershell -NoProfile` to bypass profile
- Check profile syntax: `Get-Content $PROFILE`
- Re-run Claude Code setup if needed

## System Status

Once launched, you'll see:

```
========================================================================
              ALL SYSTEMS OPERATIONAL
========================================================================
```

### ARES Status:
- Two windows opened:
  1. Ares WhatsApp Bridge (port 5000)
  2. Ares Daemon (auto-processor)

Send a WhatsApp message to test!

## Notes

- The profile runs every time you open PowerShell
- You can have multiple PowerShell windows with independent sessions
- ARES windows can be minimized to run in background
- Claude Code runs in the main terminal window

## Quick Reference

| Command | Action |
|---------|--------|
| `powershell` | Open new terminal with auto-start prompt |
| `powershell -NoProfile` | Open terminal without auto-start |
| `Start-ClaudeCode` | Manually launch Claude Code |
| `Start-Ares` | Manually launch ARES |
| `notepad $PROFILE` | Edit PowerShell profile |
| `$PROFILE` | Show profile path |

---

**Setup Complete! Open a new PowerShell terminal to see it in action.**
