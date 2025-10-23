# Xero MCP Integration for Ares System

This directory contains the Xero Model Context Protocol (MCP) server integration, allowing natural language interaction with your Xero accounting data through Claude Desktop and other MCP clients.

## 🎯 What This Does

Enables you to:
- Query Xero data using natural language
- Create/update invoices, contacts, payments via AI
- Generate financial reports on demand
- Automate accounting workflows
- Access 30+ Xero operations through Claude Desktop

## 📦 Installation Status

✅ **Package Installed:** `@xeroapi/xero-mcp-server` v0.0.12
✅ **Node.js:** v22.20.0
✅ **Dependencies:** Installed

## 🚀 Quick Start

### 1. Get Xero Credentials

```bash
# Open Xero Developer Portal
start https://developer.xero.com/app/manage
```

Follow the steps in `SETUP_GUIDE.md` to:
1. Create a Xero Developer account
2. Create a "Custom Connection" app
3. Get your Client ID and Client Secret

### 2. Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
notepad .env
```

### 3. Test Setup

```bash
node test-xero-connection.js
```

### 4. Configure Claude Desktop

The test script will output the exact configuration needed for Claude Desktop.

Add to: `%APPDATA%\Claude\claude_desktop_config.json`

### 5. Restart Claude Desktop

After adding the configuration, restart Claude Desktop to load the Xero MCP server.

## 📚 Documentation

- **SETUP_GUIDE.md** - Complete setup instructions
- **.env.example** - Environment variable template
- **test-xero-connection.js** - Connection test script

## 🛠️ Available Commands

Once configured, use natural language in Claude Desktop:

### Invoices
- "Show me all unpaid invoices"
- "Create an invoice for [customer] for $[amount]"
- "List invoices from last month"
- "Update invoice [number] to mark as paid"

### Contacts
- "List all customers"
- "Create a new contact named [name]"
- "Show contacts in [city]"

### Reports
- "Show profit and loss for this quarter"
- "Get the balance sheet"
- "Show trial balance"

### Payments
- "List payments this month"
- "Record a payment for invoice [number]"

### Bank Transactions
- "Show recent bank transactions"
- "List unreconciled transactions"

## 🔒 Security

- ✅ `.env` file in `.gitignore` (never commit credentials)
- ✅ Custom Connections are for development/personal use
- ⚠️ Your Xero data will be processed by the AI model
- 💡 Use Xero Demo Company for testing

## 📊 MCP Tools Available (30+)

<details>
<summary>View all available tools</summary>

**List Operations:**
- list-accounts
- list-contacts
- list-credit-notes
- list-invoices
- list-items
- list-organisation-details
- list-profit-and-loss
- list-quotes
- list-tax-rates
- list-payments
- list-trial-balance
- list-bank-transactions
- list-payroll-employees
- list-report-balance-sheet

**Create Operations:**
- create-contact
- create-credit-note
- create-invoice
- create-payment
- create-quote

**Update Operations:**
- update-contact
- update-invoice
- update-quote
- update-credit-note

**Payroll Operations:**
- list-payroll-employee-leave
- list-payroll-employee-leave-balances
- create-payroll-timesheet
- approve-payroll-timesheet
- and more...

</details>

## 🎓 Example Workflows

### Monthly Invoicing
```
You: "Show me all unpaid invoices from last month"
Claude: [Lists invoices with amounts and due dates]

You: "Send reminders for invoices over $500"
Claude: [Can help draft reminder emails or create follow-up tasks]
```

### Expense Tracking
```
You: "Show bank transactions from this week"
Claude: [Lists recent transactions]

You: "Create expenses for the unrecorded transactions"
Claude: [Helps categorize and record expenses]
```

### Financial Reporting
```
You: "Give me a profit and loss summary for Q4"
Claude: [Retrieves and summarizes P&L report]

You: "Compare it to Q3"
Claude: [Can analyze trends and differences]
```

## 🔗 Integration with Ares System

This Xero MCP can be integrated with the Ares WhatsApp system to:
- Receive accounting queries via WhatsApp
- Generate reports on demand
- Automate invoice creation from messages
- Send financial alerts

See `ARES_INTEGRATION.md` (coming soon) for details.

## 📝 Rate Limits

Xero API limits (2025):
- 60 calls per minute
- 5,000 calls per day
- Maximum 5 concurrent requests

The MCP server handles rate limiting automatically.

## 🐛 Troubleshooting

**"Invalid client credentials"**
- Check CLIENT_ID and CLIENT_SECRET in .env
- Regenerate secret if needed from Xero Developer Portal

**"Scope not authorized"**
- Ensure all required scopes are selected in your Custom Connection
- Required: accounting.transactions, accounting.contacts, accounting.settings

**"No organizations found"**
- Authenticate with Xero first (happens automatically on first use)
- Check you have access to at least one Xero organization

**MCP not appearing in Claude Desktop**
- Verify JSON syntax in claude_desktop_config.json
- Check Claude Desktop logs: `%APPDATA%\Claude\logs\`
- Restart Claude Desktop

## 🌐 Resources

- [Xero Developer Portal](https://developer.xero.com/)
- [Xero API Documentation](https://developer.xero.com/documentation/)
- [Xero MCP Server GitHub](https://github.com/XeroAPI/xero-mcp-server)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## 📄 License

This integration uses the official Xero MCP server which is MIT licensed.

---

**Status:** ✅ Ready for credential configuration
**Next Step:** Get your Xero Developer credentials and configure `.env`
