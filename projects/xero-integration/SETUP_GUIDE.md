# Xero MCP Server Setup Guide

## Status: Package Installed ✅

The official Xero MCP server package has been installed successfully.

**Package:** `@xeroapi/xero-mcp-server` v0.0.12
**Location:** `C:\Users\riord\xero-integration`
**Node.js:** v22.20.0 ✅ (requires v18+)

---

## Next Steps: Get Xero Developer Credentials

### Step 1: Create Xero Developer Account

1. Go to: https://developer.xero.com/
2. Click "Get Started" or "Sign In"
3. Sign up with your email (or use existing Xero account)
4. Verify your email

### Step 2: Create a Custom Connection App

1. Once logged in, go to: https://developer.xero.com/app/manage
2. Click "New app"
3. Select **"Custom Connection"** (not OAuth 2.0 app)
4. Fill in the details:
   - **App name:** "Ares Xero MCP Integration"
   - **Company or application URL:** http://localhost:3000
   - **Redirect URI:** http://localhost:3000/callback
   - **Scopes:** Select ALL of the following:
     - ✅ `accounting.transactions` (read/write invoices, bills, transactions)
     - ✅ `accounting.contacts` (read/write customers and suppliers)
     - ✅ `accounting.settings` (read organization settings)
     - ✅ `accounting.reports.read` (access financial reports)
     - ✅ `offline_access` (refresh tokens)
5. Click "Create app"

### Step 3: Get Your Credentials

After creating the app:
1. You'll see your **Client ID** - copy this
2. Click "Generate a secret" to get your **Client Secret** - copy this
3. **IMPORTANT:** Save these immediately - the secret is only shown once!

### Step 4: Configure Environment Variables

Create a `.env` file in `C:\Users\riord\xero-integration\`:

```env
XERO_CLIENT_ID=your-client-id-here
XERO_CLIENT_SECRET=your-client-secret-here
```

Replace `your-client-id-here` and `your-client-secret-here` with your actual credentials.

### Step 5: Test the Connection

Run the test script (I'll create this next):
```bash
cd C:\Users\riord\xero-integration
node test-xero-connection.js
```

---

## Claude Desktop Configuration

Once you have credentials, add this to your Claude Desktop config:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "xero": {
      "command": "npx",
      "args": ["-y", "@xeroapi/xero-mcp-server"],
      "env": {
        "XERO_CLIENT_ID": "your-client-id-here",
        "XERO_CLIENT_SECRET": "your-client-secret-here"
      }
    }
  }
}
```

Then restart Claude Desktop.

---

## Testing with Xero Demo Company

Xero provides a demo company for testing:
1. Log into https://login.xero.com/
2. Create a "Demo Company" (free, no credit card needed)
3. Use this for testing - it has sample data pre-populated

---

## Available Commands (30+)

Once configured, you can use natural language in Claude Desktop:

**Invoices:**
- "Show me all unpaid invoices"
- "Create an invoice for ABC Corp for $1,500"
- "List invoices from last month"

**Contacts:**
- "Show all customers in Sydney"
- "Create a new contact named John Smith"
- "Update contact details for ABC Corp"

**Reports:**
- "Show me the profit and loss report"
- "Get the balance sheet"
- "Show trial balance for this quarter"

**Payments:**
- "List all payments this month"
- "Record a payment for invoice INV-001"

**Bank Transactions:**
- "Show recent bank transactions"
- "List unreconciled transactions"

---

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` files to git
- Keep your client secret secure
- Use Demo Company for testing first
- Your Xero data will be processed by the AI model
- Custom Connections are for development/personal use only
- For production apps, use full OAuth 2.0 flow

---

## Troubleshooting

**Issue:** "Invalid client credentials"
- Check that CLIENT_ID and CLIENT_SECRET are correct
- Ensure no extra spaces in .env file
- Regenerate secret if needed

**Issue:** "Scope not authorized"
- Verify you selected all required scopes when creating the app
- Delete and recreate the custom connection with proper scopes

**Issue:** "Rate limit exceeded"
- Xero allows 60 calls/minute, 5000/day
- Wait a few minutes before retrying

---

## Next Steps

I'll create:
1. `.env.example` file as a template
2. `test-xero-connection.js` to test the setup
3. Helper scripts for common operations

Ready to proceed once you have your Xero credentials!
