# Configure ARES MCP in Claude Desktop

## Step 1: Locate Claude Desktop Config

The config file is at:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Or navigate to:
```
C:\Users\riord\AppData\Roaming\Claude\claude_desktop_config.json
```

## Step 2: Add ARES MCP Server

Open `claude_desktop_config.json` and add:

```json
{
  "mcpServers": {
    "ares": {
      "command": "node",
      "args": [
        "C:\\Users\\riord\\ares-mcp-server\\dist\\index.js"
      ]
    }
  }
}
```

**If you already have other MCP servers**, add ARES to the existing `mcpServers` object:

```json
{
  "mcpServers": {
    "playwright-chrome": {
      "command": "node",
      "args": ["C:\\Users\\riord\\.ares-mcp\\mcp-playwright-chrome\\dist\\index.js"],
      "disabled": false,
      "alwaysAllow": []
    },
    "ares": {
      "command": "node",
      "args": [
        "C:\\Users\\riord\\ares-mcp-server\\dist\\index.js"
      ]
    }
  }
}
```

## Step 3: Restart Claude Desktop

1. Completely close Claude Desktop
2. Reopen it
3. ARES tools should now be available

## Step 4: Test It

In Claude Desktop, try:

```
Use the get_proven_patterns tool to show me all Tier 1 patterns
```

You should see Claude call the ARES MCP and return your proven patterns.

---

## Verification

Check if ARES is loaded:
1. Open Claude Desktop
2. Look for MCP tools icon
3. Should see: `get_proven_patterns`, `validate_approach`, `recommend_pattern`, `query_tech_success`

---

## Troubleshooting

### Tools Not Showing

**Check MCP logs:**
```
%APPDATA%\Claude\logs\mcp.log
```

**Common issues:**
- Path to `dist/index.js` incorrect (check backslashes)
- Server not built (`cd ares-mcp-server && npm run build`)
- Node.js not in PATH

### Server Crashes

**Test manually:**
```bash
cd ares-mcp-server
node dist/index.js
```

Should output:
```
ARES MCP Server v2.5 running on stdio
```

If it crashes, check:
- Node.js version (need 18+)
- TypeScript compiled successfully
- Paths to proven-patterns.md correct

---

## Next Steps

Once ARES MCP is working:

1. **Test All Tools** - Try each of the 4 tools in Claude Desktop
2. **Use in Real Tasks** - Ask Claude to help with coding tasks using ARES patterns
3. **Provide Feedback** - Note what works well, what needs improvement
4. **Phase 1 Ready** - Once this is solid, add meta-agent decomposition capability

---

**Status:** Foundation Complete → Ready for Phase 1 (Meta-Agent)
