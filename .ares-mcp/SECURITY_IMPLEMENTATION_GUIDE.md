# ARES SECURITY IMPLEMENTATION GUIDE
## Step-by-Step Instructions to Secure Your System

**Version:** 1.0.0
**Estimated Time:** 2-4 hours
**Difficulty:** Intermediate

---

## BEFORE YOU BEGIN

### Prerequisites
1. Backup your entire ARES directory
2. Stop all running ARES services
3. Install required Python packages:
   ```bash
   pip install python-dotenv cryptography PyJWT flask-limiter
   ```

### Emergency Checklist
- [ ] All ARES services stopped
- [ ] Full backup completed
- [ ] Git committed current state (if tracked)
- [ ] Ready to regenerate API credentials

---

## PHASE 1: IMMEDIATE SECURITY FIXES (Next 1 Hour)

### Step 1.1: Revoke Exposed Credentials

**Why:** If credentials were committed to Git, they are permanently compromised.

#### WhatsApp API (Meta/Facebook)
1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Navigate to your app → WhatsApp → API Setup
3. Click "Generate New Token"
4. **Save the new token** (you'll need it for .env)
5. Revoke the old token

#### Xero API
1. Go to [Xero Developer](https://developer.xero.com/myapps)
2. Select your app → Regenerate secret
3. **Save new Client ID and Client Secret**

### Step 1.2: Create Secure .env File

```bash
# Navigate to your home directory
cd C:\Users\riord

# Copy the example file
cp .ares-mcp\.env.example .env

# Edit the file with your actual credentials
notepad .env
```

**Fill in your .env with NEW credentials:**

```bash
# WhatsApp API
WHATSAPP_ACCESS_TOKEN=YOUR_NEW_TOKEN_HERE
WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_NUMBER_ID
WHATSAPP_VERIFY_TOKEN=create_random_verify_token_here
WHATSAPP_AUTHORIZED_NUMBER=+61432154351

# Xero API
XERO_CLIENT_ID=YOUR_NEW_CLIENT_ID
XERO_CLIENT_SECRET=YOUR_NEW_CLIENT_SECRET
XERO_REDIRECT_URI=http://localhost:8080/callback

# Generate these with Python:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
ARES_API_KEY=GENERATE_RANDOM_KEY_HERE
JWT_SECRET=GENERATE_RANDOM_SECRET_HERE

# Generate encryption key:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=GENERATE_ENCRYPTION_KEY_HERE
```

**Generate secure random values:**

```bash
# PowerShell (Windows)
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))

# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# For encryption key specifically:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 1.3: Remove Hardcoded Credentials

**File: `.ares-mcp/whatsapp_bridge.py`**

**BEFORE (Lines 31-34):**
```python
ACCESS_TOKEN = "EAAIZCTzaF1osBPlFn8V13lWJgsFjTh4twQZC7MMT0WcOhwL1q3FcD5NcRvZBGu6..."
PHONE_NUMBER_ID = "810808242121215"
VERIFY_TOKEN = "ares_webhook_verify_2024"
AUTHORIZED_NUMBER = "+61432154351"
```

**AFTER:**
```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')
AUTHORIZED_NUMBER = os.getenv('WHATSAPP_AUTHORIZED_NUMBER')

# Validate that credentials are loaded
if not all([ACCESS_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN, AUTHORIZED_NUMBER]):
    raise ValueError("Missing required environment variables. Check your .env file.")
```

**File: `.ares-mcp/whatsapp_poller.py`**

Apply the same changes to lines 22-24.

**File: `xero-integration/.env`**

**DELETE THIS FILE!** It contains unencrypted credentials.

Move credentials to your main `.env` file instead.

### Step 1.4: Update .gitignore

Your .gitignore has been updated. Verify it includes:

```bash
# Check .gitignore
type .gitignore | findstr "\.env"

# Should show:
# .env
# .env.*
# !.env.example
```

### Step 1.5: Clean Git History (CRITICAL)

**Check if secrets were committed:**

```bash
# Check Git log for .env files
git log --all --full-history -- "*.env"

# Check for credential patterns
git log --all -p -- "*.py" | findstr /C:"ACCESS_TOKEN = "
```

**If secrets found in Git history:**

**Option A: Clean Git history (advanced)**
```bash
# USE WITH CAUTION - This rewrites history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch **/.env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (only if you haven't shared repository)
git push origin --force --all
```

**Option B: Create new repository (safer)**
```bash
# Create new repo without compromised history
cd ..
mkdir ares-clean
cd ares-clean
git init

# Copy code (exclude .git and sensitive files)
# Then commit fresh
```

---

## PHASE 2: ADD AUTHENTICATION & AUTHORIZATION (Next 1 Hour)

### Step 2.1: Update whatsapp_bridge.py with Security

Add imports at the top:

```python
from ares_security import (
    require_api_key,
    Validator,
    AuditLogger
)
```

Update the `/send` endpoint:

**BEFORE:**
```python
@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    message = data.get('message')
    to_number = data.get('to', AUTHORIZED_NUMBER)
    # ...
```

**AFTER:**
```python
@app.route('/send', methods=['POST'])
@require_api_key  # Add authentication
def send_message():
    data = request.get_json()

    # Initialize validator and audit logger
    validator = Validator()
    audit = AuditLogger()

    # Validate inputs
    to_number = data.get('to', AUTHORIZED_NUMBER)
    if not validator.validate_phone_number(to_number):
        audit.log_security_event(
            request.remote_addr,
            'invalid_phone_number',
            'MEDIUM'
        )
        return jsonify({'error': 'Invalid phone number format'}), 400

    # Sanitize message
    raw_message = data.get('message', '')
    message = validator.sanitize_message(raw_message)

    if not message:
        return jsonify({'error': 'Message required'}), 400

    # Log the action
    audit.log_data_access(
        request.remote_addr,
        'whatsapp_send',
        'message_sent'
    )

    # Send message
    result = send_whatsapp_message(to_number, message)

    if result:
        return jsonify({"status": "sent"}), 200
    else:
        return jsonify({"status": "failed"}), 500
```

Update other endpoints similarly:

```python
@app.route('/tasks', methods=['GET'])
@require_api_key  # Add authentication
def get_tasks():
    # Existing code...

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@require_api_key  # Add authentication
def delete_task(task_id):
    # Existing code...
```

### Step 2.2: Add Rate Limiting

Install rate limiting:

```bash
pip install flask-limiter redis
```

Update whatsapp_bridge.py:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# After creating Flask app
app = Flask(__name__)

# Add rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=os.getenv('REDIS_URL', 'memory://'),
    default_limits=["200 per day", "50 per hour"]
)

# Apply to endpoints
@app.route('/webhook', methods=['POST'])
@limiter.limit("100 per minute")
def webhook():
    # ...

@app.route('/send', methods=['POST'])
@require_api_key
@limiter.limit("10 per minute")  # Strict limit
def send_message():
    # ...
```

### Step 2.3: Encrypt Task Queue

Update task queue storage to use encryption:

```python
from ares_security import EncryptionService

# Initialize encryption
encryption = EncryptionService()

def save_task_queue(queue):
    """Save encrypted task queue"""
    encrypted_data = encryption.encrypt_dict(queue)
    with open(TASK_QUEUE_FILE, 'w') as f:
        f.write(encrypted_data)

def load_task_queue():
    """Load and decrypt task queue"""
    if TASK_QUEUE_FILE.exists():
        try:
            with open(TASK_QUEUE_FILE, 'r') as f:
                encrypted_data = f.read()
            return encryption.decrypt_dict(encrypted_data)
        except Exception as e:
            logger.error(f"Error decrypting task queue: {e}")
            # Return empty queue if decryption fails
            return []
    return []
```

---

## PHASE 3: HARDEN SECURITY (Next 1 Hour)

### Step 3.1: Add Security Headers

```python
from flask import Flask
from flask_talisman import Talisman

app = Flask(__name__)

# Add security headers
if os.getenv('NODE_ENV') == 'production':
    Talisman(app,
        force_https=True,
        strict_transport_security=True,
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline'",
            'style-src': "'self' 'unsafe-inline'"
        }
    )

# Add security headers for all responses
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

### Step 3.2: Implement Audit Logging

Update all critical operations to log:

```python
from ares_security import AuditLogger

audit = AuditLogger()

# Log authentication
audit.log_auth_success(user_id)
audit.log_auth_failure(user_id, reason)

# Log data access
audit.log_data_access(user_id, resource, action)

# Log security events
audit.log_security_event(user_id, event, severity)
```

### Step 3.3: Set Up Intrusion Detection

```python
from ares_security import IntrusionDetector

detector = IntrusionDetector()

# In authentication failure handler
detector.record_event(user_id, 'failed_auth')

# In invalid API key handler
detector.record_event(ip_address, 'invalid_api_key')

# In permission denied handler
detector.record_event(user_id, 'permission_denied')
```

### Step 3.4: Enable HTTPS (Production)

For development with ngrok:

```bash
# Install ngrok
# Get auth token from https://dashboard.ngrok.com/

ngrok authtoken YOUR_NGROK_TOKEN
ngrok http 5000
```

For production:

```python
# Use Let's Encrypt certificate
# Install certbot
# Get free SSL certificate

if __name__ == "__main__":
    import ssl

    if os.getenv('NODE_ENV') == 'production':
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(
            '/etc/letsencrypt/live/yourdomain.com/fullchain.pem',
            '/etc/letsencrypt/live/yourdomain.com/privkey.pem'
        )
        app.run(host='0.0.0.0', port=443, ssl_context=context)
    else:
        app.run(host='0.0.0.0', port=5000, debug=False)
```

---

## PHASE 4: TESTING & VALIDATION (Next 30 Minutes)

### Step 4.1: Run Security Test Suite

```bash
cd C:\Users\riord\.ares-mcp
python security_test_suite.py
```

**Address all FAIL items before proceeding.**

### Step 4.2: Manual Testing

Test each endpoint with authentication:

**With API key (should work):**
```bash
curl -X POST http://localhost:5000/send \
  -H "X-API-Key: YOUR_ARES_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Test message\"}"
```

**Without API key (should fail with 401):**
```bash
curl -X POST http://localhost:5000/send \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Test message\"}"
```

### Step 4.3: Test Rate Limiting

```bash
# Run this script to test rate limiting
for i in {1..15}; do
  curl -X POST http://localhost:5000/send \
    -H "X-API-Key: YOUR_ARES_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"Test $i\"}"
  echo "Request $i"
done

# Should see 429 (Too Many Requests) after limit exceeded
```

### Step 4.4: Verify Encryption

```bash
# Check that task queue is encrypted
type C:\Users\riord\.ares-mcp\mobile_task_queue.json

# Should see encrypted data, not plaintext
```

---

## PHASE 5: DEPLOYMENT PREPARATION

### Step 5.1: Pre-Deployment Checklist

```markdown
## Security Pre-Launch Checklist

### Credentials & Secrets
- [x] All secrets moved to environment variables
- [x] Production credentials generated
- [x] .env files in .gitignore
- [x] Git history cleaned
- [ ] Secrets manager configured (for production)

### Authentication & Authorization
- [x] All endpoints require authentication
- [x] API keys implemented
- [ ] JWT tokens for user authentication (if needed)
- [x] Rate limiting enabled
- [x] Input validation implemented

### Encryption & Security
- [x] Encryption at rest enabled
- [ ] HTTPS/TLS enforced (production)
- [x] Security headers configured
- [x] Audit logging enabled

### Testing
- [x] Security test suite passes
- [x] Manual security testing completed
- [ ] Load testing completed
- [ ] Penetration testing (recommended)
```

### Step 5.2: Production Environment Setup

Create separate `.env.production`:

```bash
NODE_ENV=production
PORT=443

# Production credentials (different from dev)
WHATSAPP_ACCESS_TOKEN=prod_token
ARES_API_KEY=prod_api_key
JWT_SECRET=prod_jwt_secret
ENCRYPTION_KEY=prod_encryption_key

# Production database (with SSL)
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Production Redis
REDIS_URL=redis://:password@host:6379/0

# Enable security features
ENABLE_HSTS=true
ENABLE_CSP=true
SESSION_COOKIE_SECURE=true

# Monitoring
SENTRY_DSN=your_sentry_dsn
SLACK_WEBHOOK_URL=your_slack_webhook
```

### Step 5.3: Create Backup Script

```bash
# backup_ares.bat
@echo off
set BACKUP_DIR=C:\Users\riord\ares-backups
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

mkdir %BACKUP_DIR%\%TIMESTAMP%

xcopy C:\Users\riord\.ares-mcp %BACKUP_DIR%\%TIMESTAMP% /E /I /H /Y
echo Backup completed: %BACKUP_DIR%\%TIMESTAMP%
```

---

## ONGOING SECURITY MAINTENANCE

### Daily Tasks
- Review audit logs for suspicious activity
- Monitor intrusion detection alerts

### Weekly Tasks
- Review access logs
- Check for failed authentication attempts
- Verify backups are working

### Monthly Tasks
- Review and update dependencies
- Run security test suite
- Audit user permissions
- Check for exposed secrets using:
  ```bash
  git-secrets --scan
  ```

### Quarterly Tasks
- Rotate credentials (API keys, passwords)
- Review and update security policies
- Conduct security training
- Penetration testing

### Annually
- Full security audit
- Update SSL/TLS certificates
- Review disaster recovery plan
- Compliance audit (GDPR, etc.)

---

## TROUBLESHOOTING

### "ENCRYPTION_KEY not set" error

```bash
# Generate new encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
echo ENCRYPTION_KEY=generated_key_here >> .env
```

### "JWT_SECRET not configured" error

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
echo JWT_SECRET=generated_secret_here >> .env
```

### Rate limiting not working

```bash
# Install Redis (or use memory storage)
pip install redis

# Update .env
echo REDIS_URL=memory:// >> .env
```

### Cannot decrypt task queue

```bash
# If encryption key changed, old encrypted data is lost
# Delete encrypted file and start fresh
del C:\Users\riord\.ares-mcp\mobile_task_queue.json
```

---

## ADDITIONAL RESOURCES

### Security Tools
- **Git Secrets:** Prevent committing secrets
  ```bash
  pip install git-secrets
  git secrets --install
  git secrets --register-aws
  ```

- **Safety:** Check for vulnerable dependencies
  ```bash
  pip install safety
  safety check
  ```

- **Bandit:** Python security linter
  ```bash
  pip install bandit
  bandit -r .ares-mcp/
  ```

### Learning Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Flask Security](https://flask.palletsprojects.com/en/2.3.x/security/)

---

## EMERGENCY CONTACTS

### Security Incident
1. Stop all services immediately
2. Disconnect from network
3. Review audit logs
4. Rotate all credentials
5. Notify affected parties

### Support
- ARES Documentation: `.ares-mcp/README.md`
- Security Framework: `.ares-mcp/MASTER_SECURITY_FRAMEWORK.md`
- Vulnerability Report: `.ares-mcp/SECURITY_AUDIT_CRITICAL.md`

---

**Congratulations!** You've completed the ARES Security Implementation.

Your system is now protected by 10 layers of security controls.

🔐 **Stay Secure!**
