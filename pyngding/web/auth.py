"""BasicAuth implementation using PBKDF2."""
import hashlib
import hmac
from typing import Optional


def parse_password_hash(hash_str: str) -> Optional[tuple]:
    """Parse a PBKDF2 password hash string.
    
    Format: pbkdf2:sha256:iterations:salt_hex:hash_hex
    
    Returns (algorithm, iterations, salt_bytes, hash_bytes) or None if invalid.
    """
    try:
        parts = hash_str.split(':')
        if len(parts) != 5 or parts[0] != 'pbkdf2':
            return None
        
        algorithm = parts[1]
        iterations = int(parts[2])
        salt_hex = parts[3]
        hash_hex = parts[4]
        
        salt = bytes.fromhex(salt_hex)
        hash_bytes = bytes.fromhex(hash_hex)
        
        return (algorithm, iterations, salt, hash_bytes)
    except (ValueError, IndexError):
        return None


def verify_password(password: str, hash_str: str) -> bool:
    """Verify a password against a PBKDF2 hash.
    
    Uses constant-time comparison via hmac.compare_digest.
    """
    parsed = parse_password_hash(hash_str)
    if not parsed:
        return False
    
    algorithm, iterations, salt, expected_hash = parsed
    
    # Compute hash
    computed_hash = hashlib.pbkdf2_hmac(
        algorithm,
        password.encode('utf-8'),
        salt,
        iterations
    )
    
    # Constant-time comparison
    return hmac.compare_digest(computed_hash, expected_hash)


def check_basic_auth(auth_header: Optional[str], username: str, password_hash: str) -> bool:
    """Check BasicAuth header against credentials.
    
    Returns True if authentication succeeds, False otherwise.
    """
    if not auth_header:
        return False
    
    if not auth_header.startswith('Basic '):
        return False
    
    try:
        import base64
        encoded = auth_header[6:]  # Remove "Basic " prefix
        decoded = base64.b64decode(encoded).decode('utf-8')
        user, password = decoded.split(':', 1)
        
        if user != username:
            return False
        
        return verify_password(password, password_hash)
    except Exception:
        return False


def require_auth(func):
    """Decorator to require BasicAuth for a route."""
    def wrapper(*args, **kwargs):
        from bottle import request, response
        from pyngding.core.config import Config
        
        # Get config from app context (we'll pass it via closure)
        # For now, we'll check it in the web.py route handlers
        return func(*args, **kwargs)
    return wrapper

