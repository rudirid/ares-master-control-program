# ARES SECURITY QUICK REFERENCE
**Last Updated:** 2025-10-15

---

## 🚨 CRITICAL FILES - READ THESE FIRST

1. **SECURITY_AUDIT_CRITICAL.md** - List of vulnerabilities found in your system
2. **SECURITY_IMPLEMENTATION_GUIDE.md** - Step-by-step fixes (2-4 hours)
3. **MASTER_SECURITY_FRAMEWORK.md** - Complete security architecture reference

---

## ⚡ QUICK START (5 Minutes)

### 1. Stop All Services
```bash
# Close all ARES windows or press Ctrl+C in each terminal
```

### 2. Create .env File
```bash
cd C:\Users\riord
cp .ares-mcp\.env.example .env
notepad .env
```

### 3. Generate Secrets
```powershell
# API Key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption Key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Update Credentials in .env
Fill in your .env with the generated secrets and your API credentials.

### 5. Run Security Test
```bash
cd C:\Users\riord\.ares-mcp
python security_test_suite.py
```

---

## 🔑 COMMON COMMANDS

### Generate Secure Keys
```bash
# Random API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption key (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# PowerShell alternative
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

### Check for Exposed Secrets
```bash
# Check Git history for .env files
git log --all --full-history -- "*.env"

# Check for hardcoded credentials
git log --all -p -- "*.py" | findstr "ACCESS_TOKEN"

# Scan for secrets (requires git-secrets)
git secrets --scan
```

### Test API Security
```bash
# Test without authentication (should fail)
curl http://localhost:5000/send

# Test with authentication (should work)
curl -X POST http://localhost:5000/send \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"test\"}"
```

### Run Security Tests
```bash
# Full security test suite
python C:\Users\riord\.ares-mcp\security_test_suite.py

# Check dependencies for vulnerabilities
pip install safety
safety check

# Python security linter
pip install bandit
bandit -r C:\Users\riord\.ares-mcp\
```

---

## 📝 CHECKLIST: BEFORE PUBLIC LAUNCH

### Credentials
- [ ] All secrets in environment variables (no hardcoding)
- [ ] Production credentials different from dev
- [ ] .env files not in Git
- [ ] Git history cleaned of secrets
- [ ] API keys rotated after any exposure

### Authentication
- [ ] All API endpoints require authentication
- [ ] Rate limiting enabled (10-100 req/min)
- [ ] Input validation on all user inputs
- [ ] Permission checks for sensitive operations

### Encryption
- [ ] Data at rest encrypted (task queues, logs)
- [ ] HTTPS/TLS enabled in production
- [ ] Strong encryption keys (32+ bytes)
- [ ] Database connections use SSL

### Monitoring
- [ ] Audit logging enabled
- [ ] Intrusion detection configured
- [ ] Security alerts set up (email/Slack)
- [ ] Log retention policy defined

### Testing
- [ ] Security test suite passes (>90%)
- [ ] Manual penetration testing done
- [ ] Load testing completed
- [ ] Backup/restore tested

---

## 🔒 SECURITY LAYERS

Your ARES system should have these 10 protection layers:

1. ✅ **Secrets Management** - Environment variables, no hardcoding
2. ✅ **Authentication** - API keys, JWT tokens
3. ✅ **Input Validation** - Sanitize all user inputs
4. ✅ **Rate Limiting** - Prevent abuse (10-100 req/min)
5. ✅ **Encryption** - Data at rest (AES-256) and in transit (TLS)
6. ✅ **Audit Logging** - Track all activities
7. ✅ **Database Security** - SSL, row-level security, encryption
8. ✅ **Security Headers** - HSTS, CSP, X-Frame-Options
9. ✅ **Intrusion Detection** - Alert on suspicious activity
10. ✅ **Incident Response** - Plan for breaches

---

## 🚨 EMERGENCY PROCEDURES

### If Credentials Exposed
1. **Stop all services immediately**
2. Regenerate all API keys (WhatsApp, Xero, etc.)
3. Update .env with new credentials
4. Review logs for unauthorized access
5. Notify affected parties if data breached

### If System Compromised
1. **Disconnect from network**
2. Stop all services
3. Review audit logs
4. Restore from clean backup
5. Rotate ALL credentials
6. Run security scan
7. Document incident

---

## 📚 DOCUMENTATION STRUCTURE

```
.ares-mcp/
├── SECURITY_AUDIT_CRITICAL.md          # What's vulnerable
├── MASTER_SECURITY_FRAMEWORK.md        # Security architecture
├── SECURITY_IMPLEMENTATION_GUIDE.md    # Step-by-step fixes
├── SECURITY_QUICK_REFERENCE.md         # This file
├── ares_security.py                    # Security module
├── security_test_suite.py              # Automated tests
├── .env.example                        # Template (commit this)
└── .gitignore                          # Protect secrets
```

---

## 🔧 TROUBLESHOOTING

### Error: "ENCRYPTION_KEY not set"
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add to .env: ENCRYPTION_KEY=<generated_key>
```

### Error: "API key required"
```bash
# Check .env file exists and has ARES_API_KEY
type C:\Users\riord\.env | findstr "ARES_API_KEY"
```

### Error: "Invalid phone number format"
```bash
# Phone numbers must be in E.164 format: +[country][number]
# Example: +61432154351 (not 0432154351)
```

### Rate Limit Exceeded (429)
```bash
# Wait for rate limit window to reset (typically 1 minute)
# Or increase limits in .env:
# RATE_LIMIT_SEND=20 per minute
```

---

## 📞 QUICK CONTACTS

### Security Issues
- Review logs: `C:\Users\riord\.ares-mcp\logs\audit.log`
- Run tests: `python security_test_suite.py`
- Read guide: `SECURITY_IMPLEMENTATION_GUIDE.md`

### API Issues
- WhatsApp: https://developers.facebook.com/
- Xero: https://developer.xero.com/
- Meta Status: https://developers.facebook.com/status/

---

## 🎯 DAILY SECURITY ROUTINE (5 Minutes)

```bash
# 1. Check audit logs for issues
type C:\Users\riord\.ares-mcp\logs\audit.log | findstr "FAIL\|ERROR\|CRITICAL"

# 2. Verify services are running securely
curl http://localhost:5000/send
# Should return 401 (authentication required)

# 3. Check for Git issues
git status | findstr "\.env"
# Should show nothing (env files not tracked)
```

---

## 📦 DEPENDENCIES

### Required Python Packages
```bash
pip install python-dotenv
pip install cryptography
pip install PyJWT
pip install flask-limiter
pip install redis  # Optional, for production rate limiting
```

### Optional Security Tools
```bash
pip install safety      # Dependency vulnerability scanner
pip install bandit      # Python security linter
pip install git-secrets # Prevent committing secrets
```

---

## 🎓 LEARNING RESOURCES

### Essential Reading
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Python Security: https://python.readthedocs.io/en/stable/library/security_warnings.html
- Flask Security: https://flask.palletsprojects.com/en/2.3.x/security/

### Advanced Topics
- JWT Best Practices: https://datatracker.ietf.org/doc/html/rfc8725
- Cryptography: https://cryptography.io/en/latest/
- GDPR Compliance: https://gdpr.eu/

---

## 🔐 SECURITY SCORE TARGETS

Based on `security_test_suite.py` results:

- **90-100%** ✅ Excellent - Production Ready
- **75-89%** 🟡 Good - Minor improvements needed
- **60-74%** ⚠️ Needs Improvement - Address failures before launch
- **<60%** 🚨 Critical - Do NOT deploy to production

**Current Status:** Run `python security_test_suite.py` to find out.

---

## 🎯 NEXT STEPS

1. Read `SECURITY_AUDIT_CRITICAL.md` to understand vulnerabilities
2. Follow `SECURITY_IMPLEMENTATION_GUIDE.md` step-by-step
3. Run `security_test_suite.py` to verify fixes
4. Deploy to production once score >90%

---

**Remember:** Security is a continuous process, not a one-time task.

🔐 **ARES Security Framework - Protecting Your Digital Assets**
