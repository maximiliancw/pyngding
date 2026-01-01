"""API key generation and verification."""
import secrets

from pyngding.core.crypto import create_pbkdf2_hash, verify_pbkdf2


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key.

    Returns:
        Tuple of (full_key, key_prefix) where key_prefix is first 8 chars.
    """
    full_key = secrets.token_urlsafe(32)
    key_prefix = full_key[:8]
    return full_key, key_prefix


def hash_api_key(key: str) -> str:
    """Hash an API key using PBKDF2.

    Args:
        key: The API key to hash

    Returns:
        Hash string in format: pbkdf2:sha256:iterations:salt_hex:hash_hex
    """
    return create_pbkdf2_hash(key)


def verify_api_key(key: str, hash_str: str) -> bool:
    """Verify an API key against its hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        key: The API key to verify
        hash_str: The stored hash string

    Returns:
        True if the key matches the hash, False otherwise.
    """
    return verify_pbkdf2(key, hash_str)
