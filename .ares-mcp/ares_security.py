"""
ARES Security Module
Comprehensive security utilities for the ARES ecosystem

Features:
- API Key Authentication
- JWT Token Management
- Input Validation & Sanitization
- Rate Limiting
- Encryption Services
- Audit Logging
- Intrusion Detection

Usage:
    from ares_security import (
        require_api_key,
        require_jwt,
        Validator,
        EncryptionService,
        AuditLogger
    )
"""

import os
import hmac
import hashlib
import re
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional
from pathlib import Path
from html import escape

# Try to import dependencies (graceful degradation if not installed)
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("WARNING: PyJWT not installed. JWT authentication disabled.")

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("WARNING: cryptography not installed. Encryption disabled.")

try:
    from flask import request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("WARNING: Flask not installed. Decorators disabled.")

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG_DIR = Path.home() / ".ares-mcp"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

LOGS_DIR = CONFIG_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def require_api_key(f):
    """
    Decorator to require API key authentication

    Usage:
        @app.route('/send', methods=['POST'])
        @require_api_key
        def send_message():
            pass

    Environment Variable:
        ARES_API_KEY: The valid API key
    """
    if not FLASK_AVAILABLE:
        return f

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            return jsonify({
                'error': 'API key required',
                'code': 'AUTH_001'
            }), 401

        # Use constant-time comparison to prevent timing attacks
        valid_key = os.getenv('ARES_API_KEY')
        if not valid_key:
            logging.error("ARES_API_KEY not set in environment")
            return jsonify({
                'error': 'Server configuration error',
                'code': 'AUTH_002'
            }), 500

        if not hmac.compare_digest(api_key, valid_key):
            # Log suspicious activity
            logger = AuditLogger()
            logger.log_auth_failure(
                request.remote_addr,
                'invalid_api_key'
            )

            # Check for intrusion detection
            detector = IntrusionDetector()
            detector.record_event(request.remote_addr, 'invalid_api_key')

            return jsonify({
                'error': 'Invalid API key',
                'code': 'AUTH_003'
            }), 401

        # Log successful authentication
        logger = AuditLogger()
        logger.log_auth_success(request.remote_addr)

        return f(*args, **kwargs)
    return decorated_function


def require_jwt(f):
    """
    Decorator to require JWT token authentication

    Usage:
        @app.route('/protected', methods=['GET'])
        @require_jwt
        def protected_resource():
            user = request.user
            return jsonify({'user_id': user['user_id']})

    Environment Variable:
        JWT_SECRET: Secret key for JWT signing
    """
    if not FLASK_AVAILABLE or not JWT_AVAILABLE:
        return f

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Token required',
                'code': 'AUTH_004'
            }), 401

        token = auth_header.replace('Bearer ', '')

        try:
            payload = verify_jwt(token)
            request.user = payload

            # Log successful authentication
            logger = AuditLogger()
            logger.log_auth_success(payload.get('user_id', 'unknown'))

            return f(*args, **kwargs)
        except AuthError as e:
            # Log authentication failure
            logger = AuditLogger()
            logger.log_auth_failure('jwt_token', str(e))

            return jsonify({
                'error': str(e),
                'code': 'AUTH_005'
            }), 401

    return decorated_function


def require_permission(permission: str):
    """
    Decorator to check user permissions

    Usage:
        @app.route('/send', methods=['POST'])
        @require_jwt
        @require_permission('message:send')
        def send_message():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'user'):
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'AUTH_006'
                }), 401

            user = request.user
            user_permissions = user.get('permissions', [])

            # Admin has all permissions
            if '*' in user_permissions:
                return f(*args, **kwargs)

            if permission not in user_permissions:
                # Log permission denied
                logger = AuditLogger()
                logger.log_security_event(
                    user.get('user_id', 'unknown'),
                    f"permission_denied: {permission}",
                    'MEDIUM'
                )

                # Track for intrusion detection
                detector = IntrusionDetector()
                detector.record_event(
                    user.get('user_id', 'unknown'),
                    'permission_denied'
                )

                return jsonify({
                    'error': 'Permission denied',
                    'code': 'AUTH_007'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

class AuthError(Exception):
    """Authentication error"""
    pass


def generate_jwt(user_id: str, permissions: list = None,
                 expiry_hours: int = 24) -> str:
    """
    Generate JWT token with expiration

    Args:
        user_id: User identifier
        permissions: List of permissions
        expiry_hours: Token expiry in hours

    Returns:
        JWT token string
    """
    if not JWT_AVAILABLE:
        raise AuthError("JWT library not available")

    payload = {
        'user_id': user_id,
        'permissions': permissions or [],
        'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
        'iat': datetime.utcnow(),
        'iss': 'ares-system'
    }

    secret = os.getenv('JWT_SECRET')
    if not secret:
        raise AuthError("JWT_SECRET not configured")

    algorithm = os.getenv('JWT_ALGORITHM', 'HS256')

    return jwt.encode(payload, secret, algorithm=algorithm)


def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Verify JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload

    Raises:
        AuthError: If token is invalid or expired
    """
    if not JWT_AVAILABLE:
        raise AuthError("JWT library not available")

    try:
        secret = os.getenv('JWT_SECRET')
        if not secret:
            raise AuthError("JWT_SECRET not configured")

        algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        payload = jwt.decode(token, secret, algorithms=[algorithm])

        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError('Token expired')
    except jwt.InvalidTokenError:
        raise AuthError('Invalid token')


# ============================================================================
# INPUT VALIDATION & SANITIZATION
# ============================================================================

class Validator:
    """Input validation and sanitization utilities"""

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Validate phone number in E.164 format

        Args:
            phone: Phone number string

        Returns:
            True if valid, False otherwise
        """
        # E.164 format: +[country code][number]
        # Example: +61432154351
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def sanitize_message(message: str, max_length: int = 4096) -> str:
        """
        Sanitize message text to prevent injection attacks

        Args:
            message: Raw message text
            max_length: Maximum message length

        Returns:
            Sanitized message
        """
        if not isinstance(message, str):
            return ""

        # Remove null bytes
        message = message.replace('\x00', '')

        # Limit length
        message = message[:max_length]

        # HTML escape to prevent XSS
        message = escape(message)

        # Remove control characters (except newline, tab, carriage return)
        message = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', message)

        return message.strip()

    @staticmethod
    def validate_url(url: str, allowed_domains: list = None) -> bool:
        """
        Validate URL and check against whitelist

        Args:
            url: URL string
            allowed_domains: List of allowed domains (optional)

        Returns:
            True if valid and allowed, False otherwise
        """
        # Basic URL validation
        url_pattern = r'^https?://[a-zA-Z0-9-_.]+\.[a-zA-Z]{2,}(/.*)?$'
        if not re.match(url_pattern, url):
            return False

        # If no whitelist provided, check environment variable
        if allowed_domains is None:
            allowed_domains_str = os.getenv('ALLOWED_DOMAINS', '')
            allowed_domains = [d.strip() for d in allowed_domains_str.split(',') if d.strip()]

        # If still no whitelist, allow all (not recommended for production)
        if not allowed_domains:
            return True

        # Extract domain and check whitelist
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        return domain in allowed_domains

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format

        Args:
            email: Email address

        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal

        Args:
            filename: Raw filename

        Returns:
            Sanitized filename
        """
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')

        # Remove dangerous characters
        filename = re.sub(r'[^\w\s.-]', '', filename)

        # Limit length
        filename = filename[:255]

        return filename.strip()


# ============================================================================
# ENCRYPTION SERVICE
# ============================================================================

class EncryptionService:
    """Handle all encryption/decryption operations"""

    def __init__(self):
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        # Load encryption key from environment
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY not set in environment")

        try:
            self.cipher = Fernet(key.encode())
        except Exception as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY: {e}")

    def encrypt(self, data: str) -> str:
        """
        Encrypt string data

        Args:
            data: Plaintext string

        Returns:
            Encrypted string (base64 encoded)
        """
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt string data

        Args:
            encrypted_data: Encrypted string

        Returns:
            Decrypted plaintext string
        """
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def encrypt_dict(self, data: dict) -> str:
        """
        Encrypt dictionary

        Args:
            data: Dictionary to encrypt

        Returns:
            Encrypted string
        """
        import json
        json_data = json.dumps(data)
        return self.encrypt(json_data)

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """
        Decrypt to dictionary

        Args:
            encrypted_data: Encrypted string

        Returns:
            Decrypted dictionary
        """
        import json
        json_data = self.decrypt(encrypted_data)
        return json.loads(json_data)

    @staticmethod
    def hash_value(value: str, salt: str = "") -> str:
        """
        Hash a value using SHA-256

        Args:
            value: Value to hash
            salt: Optional salt

        Returns:
            Hex digest of hash
        """
        salted_value = f"{salt}{value}".encode()
        return hashlib.sha256(salted_value).hexdigest()

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key

        Returns:
            Base64-encoded key suitable for ENCRYPTION_KEY
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not available")

        return Fernet.generate_key().decode()


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Comprehensive audit logging for security events"""

    def __init__(self, log_file: Path = None):
        if log_file is None:
            log_file = LOGS_DIR / "audit.log"

        self.logger = logging.getLogger('ares_audit')

        # Only add handler if not already configured
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_event(self, event_type: str, user_id: str, action: str,
                  details: Dict[str, Any] = None, sensitive: bool = False):
        """
        Log security event

        Args:
            event_type: Type of event (AUTH_SUCCESS, DATA_ACCESS, etc.)
            user_id: User identifier
            action: Action performed
            details: Additional details dictionary
            sensitive: Whether to redact sensitive info
        """
        import json

        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'action': action,
            'details': details or {}
        }

        # Add request context if available
        if FLASK_AVAILABLE:
            try:
                event['ip_address'] = request.remote_addr
                event['user_agent'] = request.headers.get('User-Agent')
            except:
                pass

        # Redact sensitive information
        if sensitive:
            event = self._redact_sensitive(event)

        self.logger.info(json.dumps(event))

    def _redact_sensitive(self, event: Dict) -> Dict:
        """Redact sensitive information from event"""
        sensitive_fields = [
            'password', 'token', 'api_key', 'secret',
            'access_token', 'refresh_token', 'authorization'
        ]

        def redact_dict(d):
            if not isinstance(d, dict):
                return d

            return {
                k: '[REDACTED]' if k.lower() in sensitive_fields else v
                for k, v in d.items()
            }

        if 'details' in event:
            event['details'] = redact_dict(event['details'])

        return event

    def log_auth_success(self, user_id: str):
        """Log successful authentication"""
        self.log_event('AUTH_SUCCESS', user_id, 'login')

    def log_auth_failure(self, user_id: str, reason: str):
        """Log failed authentication"""
        self.log_event('AUTH_FAILURE', user_id, 'login_failed',
                      {'reason': reason})

    def log_data_access(self, user_id: str, resource: str, action: str):
        """Log data access"""
        self.log_event('DATA_ACCESS', user_id, action,
                      {'resource': resource})

    def log_security_event(self, user_id: str, event: str, severity: str):
        """Log security event"""
        self.log_event('SECURITY_EVENT', user_id, event,
                      {'severity': severity})


# ============================================================================
# INTRUSION DETECTION
# ============================================================================

class IntrusionDetector:
    """Detect suspicious activities and potential intrusions"""

    def __init__(self):
        # Alert thresholds
        self.alert_threshold = {
            'failed_auth': 5,        # 5 failures in 10 minutes
            'invalid_api_key': 3,    # 3 invalid API keys in 10 minutes
            'invalid_token': 3,       # 3 invalid tokens in 10 minutes
            'permission_denied': 10   # 10 permission denials in 10 minutes
        }

        self.window_seconds = 600  # 10 minutes
        self.events = {}  # In-memory storage (use Redis in production)
        self.logger = AuditLogger()

    def record_event(self, user_id: str, event_type: str):
        """
        Record security event

        Args:
            user_id: User identifier (or IP address)
            event_type: Type of event
        """
        key = f"{event_type}:{user_id}"
        current_time = datetime.utcnow()

        # Initialize if not exists
        if key not in self.events:
            self.events[key] = []

        # Add current event
        self.events[key].append(current_time)

        # Clean old events (outside time window)
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        self.events[key] = [
            t for t in self.events[key]
            if t > cutoff_time
        ]

        # Check threshold
        count = len(self.events[key])
        threshold = self.alert_threshold.get(event_type, 999)

        if count >= threshold:
            self.trigger_alert(user_id, event_type, count)

    def trigger_alert(self, user_id: str, event_type: str, count: int):
        """
        Trigger security alert

        Args:
            user_id: User identifier
            event_type: Type of event
            count: Number of events
        """
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'event_type': event_type,
            'count': count,
            'severity': 'HIGH',
            'action_taken': 'alert_triggered'
        }

        # Log critical security alert
        self.logger.logger.critical(
            f"🚨 SECURITY ALERT: {event_type} - User: {user_id}, Count: {count}"
        )

        # TODO: Send alert via email/Slack/PagerDuty
        self._send_security_alert(alert)

    def _send_security_alert(self, alert: Dict):
        """Send security alert (implement based on your needs)"""
        # Example: Send to Slack webhook
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook:
            try:
                import requests
                requests.post(slack_webhook, json={
                    'text': f"🚨 Security Alert: {alert['event_type']} - {alert['user_id']}"
                })
            except:
                pass


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key

    Args:
        length: Key length in bytes

    Returns:
        URL-safe base64-encoded key
    """
    import secrets
    return secrets.token_urlsafe(length)


def check_password_strength(password: str) -> tuple[bool, str]:
    """
    Check password strength

    Args:
        password: Password string

    Returns:
        Tuple of (is_valid, message)
    """
    min_length = int(os.getenv('PASSWORD_MIN_LENGTH', 12))

    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"

    require_uppercase = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true'
    if require_uppercase and not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letters"

    require_lowercase = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'true').lower() == 'true'
    if require_lowercase and not any(c.islower() for c in password):
        return False, "Password must contain lowercase letters"

    require_numbers = os.getenv('PASSWORD_REQUIRE_NUMBERS', 'true').lower() == 'true'
    if require_numbers and not any(c.isdigit() for c in password):
        return False, "Password must contain numbers"

    require_special = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true'
    if require_special and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, "Password must contain special characters"

    return True, "Password meets requirements"


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Create log directory if it doesn't exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Display module status
if __name__ == "__main__":
    print("ARES Security Module")
    print("=" * 60)
    print(f"Flask Available: {FLASK_AVAILABLE}")
    print(f"JWT Available: {JWT_AVAILABLE}")
    print(f"Cryptography Available: {CRYPTO_AVAILABLE}")
    print(f"Logs Directory: {LOGS_DIR}")
    print("=" * 60)
