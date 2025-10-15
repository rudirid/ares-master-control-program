# Xero + Claude Code Integration Prompt

Copy and paste this prompt into Claude (chat or Claude Code CLI) to get help integrating Xero MCP with your development workflow.

---

## 🎯 THE PROMPT

```
I need help integrating the official Xero MCP server with Claude Code for accounting automation.

CONTEXT:
- I've installed @xeroapi/xero-mcp-server v0.0.12 in C:\Users\riord\xero-integration\
- The package is ready but needs Xero Developer OAuth credentials
- I want to use natural language to interact with my Xero accounting data
- I'm using Windows and Claude Desktop

MY GOALS:
1. Set up Xero Developer account and get OAuth credentials
2. Configure the MCP server with proper scopes
3. Integrate with Claude Desktop for natural language queries
4. Test the integration with basic commands
5. Create useful workflows for common accounting tasks

HELP ME WITH:
1. Step-by-step guide to get Xero Developer credentials
   - What type of app to create (Custom Connection vs OAuth 2.0)
   - Which scopes are required for full functionality
   - How to securely store credentials

2. Configuration best practices
   - .env file structure
   - Claude Desktop config JSON format
   - Testing the connection before full deployment

3. Example natural language commands I can use once configured
   - Invoicing workflows
   - Financial reporting
   - Contact management
   - Payment tracking

4. Common troubleshooting issues and solutions
   - Authentication errors
   - Scope permission problems
   - Rate limit handling

5. Ideas for advanced automation workflows
   - Combining Xero with other tools
   - Scheduled reports
   - Alert systems for unpaid invoices

DELIVERABLES I NEED:
- [ ] Clear step-by-step credential setup guide
- [ ] Working .env configuration template
- [ ] Claude Desktop config JSON (copy-paste ready)
- [ ] List of 10+ useful example commands
- [ ] Quick reference card for common operations
- [ ] Troubleshooting checklist

EXISTING FILES IN MY PROJECT:
- C:\Users\riord\xero-integration\README.md
- C:\Users\riord\xero-integration\SETUP_GUIDE.md
- C:\Users\riord\xero-integration\test-xero-connection.js
- C:\Users\riord\xero-integration\.env.example
- C:\Users\riord\xero-integration\package.json

Please review these files if needed and build upon them.

CONSTRAINTS:
- I'm using Windows (not Mac/Linux)
- I want to use Xero Demo Company for testing first
- Security is important - no credentials in git
- I need this to work with both Claude Desktop and Claude Code CLI

START BY:
Walking me through getting my Xero Developer credentials, step by step, with screenshots or clear descriptions of what I should see at each step.
```

---

## 📋 How to Use This Prompt

### Option 1: Claude Chat (Web)
1. Go to https://claude.ai
2. Start a new conversation
3. Copy the entire prompt above (between the ``` markers)
4. Paste and send
5. Follow Claude's step-by-step guidance

### Option 2: Claude Code CLI
1. Open Claude Code
2. Type `/chat` or start a new session
3. Paste the prompt
4. Work through the integration with Claude's help

### Option 3: Claude Desktop
1. Open Claude Desktop app
2. Start new conversation
3. Paste the prompt
4. Get help configuring the MCP server itself

---

## 🎯 What This Prompt Will Get You

Claude will help you:
1. **Navigate Xero Developer Portal** - Step-by-step credential creation
2. **Configure OAuth** - Proper scopes and security setup
3. **Set up .env** - Secure credential storage
4. **Configure Claude Desktop** - Working MCP integration
5. **Test Integration** - Verify everything works
6. **Learn Commands** - Natural language examples
7. **Build Workflows** - Automation ideas specific to your needs

---

## 💡 Pro Tips

### Make it Personal
Add these details to the prompt for better results:
- Your industry/business type
- Specific accounting tasks you do regularly
- Pain points in your current accounting workflow
- Goals for automation

### Example Customizations
```
ADDITIONAL CONTEXT:
- I run a small consulting business
- I invoice ~20 clients monthly
- I need to track unpaid invoices weekly
- I want automated P&L reports monthly
```

### Follow-up Questions
After the initial setup, ask Claude:
- "How can I create a workflow to automatically email clients with overdue invoices?"
- "Show me how to generate a monthly financial report summary"
- "Can I integrate this with my email/calendar/CRM?"

---

## 🔧 Alternative: Focused Prompts

If you just need help with one specific thing, use these shorter prompts:

### Just Credentials Setup
```
I need step-by-step help getting Xero Developer OAuth credentials for @xeroapi/xero-mcp-server.
Walk me through:
1. Creating a Xero Developer account
2. Creating a Custom Connection app
3. Selecting the right scopes
4. Getting my Client ID and Secret
5. Storing them securely in .env

I'm on Windows, new to Xero Developer Portal.
```

### Just Claude Desktop Config
```
I have Xero MCP server installed and credentials ready.
Show me exactly what to add to my Claude Desktop config at %APPDATA%\Claude\claude_desktop_config.json

My credentials:
- XERO_CLIENT_ID: [ready to paste]
- XERO_CLIENT_SECRET: [ready to paste]

Give me the exact JSON to copy-paste.
```

### Just Example Commands
```
I have Xero MCP configured in Claude Desktop.
Give me 20 useful natural language commands I can use for:
- Creating/managing invoices
- Tracking payments
- Managing contacts
- Generating reports
- Bank reconciliation

Format them as a quick reference card.
```

---

## 🚀 Next Steps After Integration

Once Xero is integrated, you can:

1. **Create Ares + Xero Workflows**
   - WhatsApp message → Create Xero invoice
   - Daily unpaid invoice alerts via WhatsApp
   - Voice/text accounting queries

2. **Build Automation Scripts**
   - Scheduled financial reports
   - Auto-categorize expenses
   - Payment reminder system

3. **Combine with Other MCPs**
   - Xero + Gmail MCP = Email invoices automatically
   - Xero + Calendar MCP = Schedule payment follow-ups
   - Xero + your future Ares MCP = Knowledge-based accounting

---

## 📚 Resources

**Documentation:**
- My setup guide: `C:\Users\riord\xero-integration\SETUP_GUIDE.md`
- Official repo: https://github.com/XeroAPI/xero-mcp-server
- Xero API docs: https://developer.xero.com/documentation/

**Support:**
- Xero Developer Forums
- MCP Discord community
- Claude support for integration issues

---

## ✅ Checklist

Before using the prompt, verify:
- [ ] Xero MCP package installed (v0.0.12)
- [ ] Node.js v18+ installed
- [ ] .env.example file exists
- [ ] You have admin access to create Xero Developer account
- [ ] Claude Desktop or Claude Code is installed

---

**Ready to integrate! Copy the main prompt and start chatting with Claude.** 🚀
