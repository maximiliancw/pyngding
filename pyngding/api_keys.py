"""API key generation and verification."""
import hashlib
import hmac
import secrets
import time
from typing import Optional, Tuple


def generate_api_key() -> Tuple[str, str]:
    """Generate a new API key.
    
    Returns (full_key, key_prefix) where key_prefix is first 8 chars.
    """
    full_key = secrets.token_urlsafe(32)
    key_prefix = full_key[:8]
    return full_key, key_prefix


def hash_api_key(key: str) -> str:
    """Hash an API key using PBKDF2.
    
    Returns hash string in format: pbkdf2:sha256:iterations:salt_hex:hash_hex
    """
    salt = secrets.token_bytes(16)
    hash_value = hashlib.pbkdf2_hmac('sha256', key.encode('utf-8'), salt, 100000)
    return f"pbkdf2:sha256:100000:{salt.hex()}:{hash_value.hex()}"


def verify_api_key(key: str, hash_str: str) -> bool:
    """Verify an API key against its hash.
    
    Uses constant-time comparison.
    """
    parsed = parse_key_hash(hash_str)
    if not parsed:
        return False
    
    algorithm, iterations, salt, expected_hash = parsed
    
    computed_hash = hashlib.pbkdf2_hmac(
        algorithm,
        key.encode('utf-8'),
        salt,
        iterations
    )
    
    return hmac.compare_digest(computed_hash, expected_hash)


def parse_key_hash(hash_str: str) -> Optional[tuple]:
    """Parse a PBKDF2 hash string.
    
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

