# Playwright MCP with Chrome Profile Guide

## Configuration Complete

Your Playwright MCP is now configured to use your **actual Chrome browser** with all your:
- ✅ Saved logins and sessions
- ✅ Open tabs
- ✅ Cookies and authentication
- ✅ Browser history
- ✅ Extensions

## Configuration File

**Location**: `C:\Users\riord\.mcp.json`

```json
{
  "mcpServers": {
    "playwright-chrome": {
      "command": "npx",
      "args": [
        "-y",
        "@automatalabs/mcp-server-playwright"
      ],
      "env": {
        "PLAYWRIGHT_BROWSER": "chromium",
        "PLAYWRIGHT_CHANNEL": "chrome",
        "PLAYWRIGHT_USER_DATA_DIR": "C:\\Users\\riord\\AppData\\Local\\Google\\Chrome\\User Data",
        "PLAYWRIGHT_HEADLESS": "false"
      }
    }
  }
}
```

## How It Works

### Key Configuration Settings

1. **PLAYWRIGHT_CHANNEL: "chrome"**
   - Uses your installed Chrome browser instead of Chromium
   - Accesses all Chrome features and extensions

2. **PLAYWRIGHT_USER_DATA_DIR**
   - Points to your Chrome profile directory
   - Contains all your sessions, logins, and cookies
   - Location: `C:\Users\riord\AppData\Local\Google\Chrome\User Data`

3. **PLAYWRIGHT_HEADLESS: "false"**
   - Opens visible Chrome window (you can see what's happening)
   - Useful for debugging and monitoring automation

## Using Playwright with Chrome in Claude Code

Once Claude Code restarts and loads the MCP server, you can:

### Example Commands

```
Navigate to Gmail using my logged-in session

Click the button at coordinates X,Y

Fill in the form using my saved credentials

Take a screenshot of the current page

Extract text from the page
```

### Advantages Over Chromium

| Feature | Chromium (Default) | Chrome with Profile |
|---------|-------------------|---------------------|
| Saved Logins | ❌ No | ✅ Yes |
| Cookies/Sessions | ❌ No | ✅ Yes |
| Open Tabs | ❌ No | ✅ Yes |
| Extensions | ❌ No | ✅ Yes |
| Browser History | ❌ No | ✅ Yes |

## Profile Selection

You have multiple Chrome profiles available:
- **Default** (primary profile)
- Profile 1, 2, 4, 6, 7, 8, 9, 11, 13, 14, 16, 17, 18, 19

The configuration currently uses the **Default** profile. To use a different profile:

### Using Profile 1 (Example)
Edit `.mcp.json` and change the user data path:
```json
"PLAYWRIGHT_USER_DATA_DIR": "C:\\Users\\riord\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1"
```

## Activating the Configuration

### Method 1: Restart Claude Code
```powershell
# Exit current session (Ctrl+C or type 'exit')
# Start new session
claude
```

### Method 2: Using /mcp Command
```
/mcp
# Then enable the playwright-chrome server
```

## Verification

Once activated, check that it's working:

```
# In Claude Code, ask:
"Can you check if playwright-chrome MCP is loaded?"

# Or use:
/mcp
```

You should see `playwright-chrome` in the list of available MCP servers.

## Security Considerations

### ⚠️ Important Notes

1. **Session Sharing**: Playwright will have access to ALL logged-in sessions in Chrome
2. **Credential Access**: Can interact with any site where you're logged in
3. **Privacy**: Can see browsing history and cookies
4. **Concurrent Use**: You can use Chrome normally while Playwright runs (separate contexts)

### Best Practices

- Only use with trusted automation tasks
- Review actions before execution
- Consider using a separate Chrome profile for automation
- Close sensitive tabs before running automation

## Advanced Configuration Options

### Headless Mode (Hidden Browser)
```json
"PLAYWRIGHT_HEADLESS": "true"
```
Browser runs in background (no visible window)

### Specific Profile
```json
"PLAYWRIGHT_USER_DATA_DIR": "C:\\Users\\riord\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1"
```
Use a different Chrome profile

### Browser Selection
```json
"PLAYWRIGHT_CHANNEL": "msedge"
```
Use Microsoft Edge instead of Chrome (with same profile structure)

## Troubleshooting

### MCP Server Not Loading
1. Restart Claude Code
2. Check `.mcp.json` syntax (valid JSON)
3. Run: `/mcp` to see server status

### Chrome Profile Not Working
1. Verify path exists: `C:\Users\riord\AppData\Local\Google\Chrome\User Data`
2. Close all Chrome windows before starting
3. Check file permissions

### Sessions Not Persisting
- Ensure `PLAYWRIGHT_USER_DATA_DIR` is set correctly
- Don't use incognito/private mode
- Check Chrome isn't set to clear data on exit

### Profile Lock Error
If you get "profile is locked":
1. Close all Chrome instances
2. Or use a different profile
3. Or run with separate user data directory

## Examples

### Navigate with Logged-In Session
```
Go to https://mail.google.com
(Will use your existing Google login)
```

### Multi-Step Task
```
1. Open Twitter
2. Navigate to my profile
3. Take screenshot
4. Close the tab
```

### Form Automation
```
Fill in the contact form at example.com
- Name: Rio
- Email: (use autofill)
- Message: "Hello from automation"
- Click submit
```

## Files Created

1. **MCP Config**: `C:\Users\riord\.mcp.json`
2. **This Guide**: `C:\Users\riord\PLAYWRIGHT_CHROME_SETUP_GUIDE.md`

## Next Steps

1. **Restart Claude Code** to load the MCP configuration
2. **Test** with a simple navigation command
3. **@mention** this guide anytime: `@PLAYWRIGHT_CHROME_SETUP_GUIDE.md`

---

**Configuration Complete!** Playwright will now use your actual Chrome browser with all your sessions and logins.

Restart Claude Code to activate.
