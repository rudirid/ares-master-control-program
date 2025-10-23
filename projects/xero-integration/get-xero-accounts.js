#!/usr/bin/env node
/**
 * Fetch Xero Accounts via Direct API
 *
 * This script uses the Xero Node SDK to authenticate and retrieve
 * the chart of accounts from your Xero organization.
 */

require('dotenv').config();
const { XeroClient } = require('xero-node');
const http = require('http');
const url = require('url');

// Configuration from .env
const CLIENT_ID = process.env.XERO_CLIENT_ID;
const CLIENT_SECRET = process.env.XERO_CLIENT_SECRET;
const REDIRECT_URI = process.env.XERO_REDIRECT_URI || 'http://localhost:8080/callback';
const PORT = 8080;

// Initialize Xero client
const xero = new XeroClient({
  clientId: CLIENT_ID,
  clientSecret: CLIENT_SECRET,
  redirectUris: [REDIRECT_URI],
  scopes: [
    'offline_access',
    'accounting.transactions',
    'accounting.contacts',
    'accounting.settings',
    'accounting.reports.read'
  ]
});

let server;

async function startOAuthFlow() {
  console.log('='.repeat(70));
  console.log('XERO ACCOUNTS FETCHER');
  console.log('='.repeat(70));
  console.log();
  console.log('Starting OAuth authentication flow...');
  console.log();

  // Get authorization URL
  const consentUrl = await xero.buildConsentUrl();

  console.log('1. Open this URL in your browser:');
  console.log();
  console.log(consentUrl);
  console.log();
  console.log('2. Login to Xero and authorize the app');
  console.log('3. You will be redirected back (page will load automatically)');
  console.log();
  console.log('Waiting for authorization...');
  console.log();

  // Start local server to receive callback
  server = http.createServer(async (req, res) => {
    try {
      const parsedUrl = url.parse(req.url, true);

      if (parsedUrl.pathname === '/callback') {
        const code = parsedUrl.query.code;

        if (code) {
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <head><title>Xero Authorization</title></head>
              <body>
                <h1>✅ Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
              </body>
            </html>
          `);

          console.log('✅ Authorization received!');
          console.log();
          console.log('Exchanging code for token...');

          // Exchange code for token
          await xero.apiCallback(req.url);

          console.log('✅ Token received!');
          console.log();

          // Fetch accounts
          await fetchAccounts();

          // Close server
          server.close();

        } else {
          res.writeHead(400, { 'Content-Type': 'text/plain' });
          res.end('Authorization failed - no code received');
          server.close();
        }
      }
    } catch (error) {
      console.error('Error handling callback:', error.message);
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Error: ' + error.message);
      server.close();
    }
  });

  server.listen(PORT, () => {
    console.log(`✓ Callback server listening on port ${PORT}`);
    console.log();

    // Try to open browser automatically
    const open = require('child_process').exec;
    open(`start "" "${consentUrl}"`, (error) => {
      if (error) {
        console.log('Could not open browser automatically.');
        console.log('Please copy and paste the URL above into your browser.');
      }
    });
  });
}

async function fetchAccounts() {
  try {
    console.log('Fetching Xero data...');
    console.log();

    // Get the active tenant (organization)
    const tokenSet = xero.readTokenSet();

    // Get connections (organizations)
    const connections = await xero.updateTenants();

    if (!connections || connections.length === 0) {
      throw new Error('No Xero organizations found. Please ensure you have access to at least one Xero organization.');
    }

    const activeTenantId = connections[0].tenantId;

    console.log('Connected to Xero organization:');
    console.log(`  Tenant ID: ${activeTenantId}`);
    console.log();

    // Fetch chart of accounts
    const accountsResponse = await xero.accountingApi.getAccounts(activeTenantId);
    const accounts = accountsResponse.body.accounts;

    console.log('='.repeat(70));
    console.log(`XERO CHART OF ACCOUNTS (${accounts.length} accounts)`);
    console.log('='.repeat(70));
    console.log();

    // Group accounts by type
    const accountsByType = {};
    accounts.forEach(account => {
      const type = account.type || 'OTHER';
      if (!accountsByType[type]) {
        accountsByType[type] = [];
      }
      accountsByType[type].push(account);
    });

    // Display accounts grouped by type
    Object.keys(accountsByType).sort().forEach(type => {
      console.log(`\n${type}:`);
      console.log('-'.repeat(70));

      accountsByType[type].forEach(account => {
        const code = account.code || 'N/A';
        const name = account.name || 'Unnamed';
        const status = account.status || 'UNKNOWN';
        const taxType = account.taxType || 'NONE';

        console.log(`  [${code.padEnd(6)}] ${name}`);
        console.log(`             Status: ${status}, Tax: ${taxType}`);
        if (account.description) {
          console.log(`             ${account.description}`);
        }
        console.log();
      });
    });

    console.log('='.repeat(70));
    console.log('✅ COMPLETE');
    console.log('='.repeat(70));

    // Save to JSON file
    const fs = require('fs');
    const outputFile = 'xero-accounts.json';
    fs.writeFileSync(outputFile, JSON.stringify(accounts, null, 2));
    console.log();
    console.log(`📄 Full data saved to: ${outputFile}`);

  } catch (error) {
    console.error('❌ Error fetching accounts:', error.message);
    if (error.response) {
      console.error('Response:', error.response.statusText);
      console.error('Details:', error.response.body);
    }
  }
}

// Start the flow
startOAuthFlow().catch(error => {
  console.error('❌ Fatal error:', error.message);
  process.exit(1);
});
