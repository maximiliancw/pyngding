"""Shared PBKDF2 cryptographic utilities.

This module provides common password/key hashing and verification functions
used by both auth.py (password authentication) and api_keys.py (API key verification).
"""
import hashlib
import hmac
import secrets

# Default iterations for PBKDF2 (OWASP recommended minimum for SHA-256)
DEFAULT_ITERATIONS = 100000


def parse_pbkdf2_hash(hash_str: str) -> tuple[str, int, bytes, bytes] | None:
    """Parse a PBKDF2 hash string.

    Format: pbkdf2:algorithm:iterations:salt_hex:hash_hex

    Args:
        hash_str: The hash string to parse

    Returns:
        Tuple of (algorithm, iterations, salt_bytes, hash_bytes) or None if invalid.
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


def create_pbkdf2_hash(data: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Create a PBKDF2 hash string from data.

    Args:
        data: The string to hash (password or API key)
        iterations: Number of PBKDF2 iterations

    Returns:
        Hash string in format: pbkdf2:sha256:iterations:salt_hex:hash_hex
    """
    salt = secrets.token_bytes(16)
    hash_value = hashlib.pbkdf2_hmac('sha256', data.encode('utf-8'), salt, iterations)
    return f"pbkdf2:sha256:{iterations}:{salt.hex()}:{hash_value.hex()}"


def verify_pbkdf2(data: str, hash_str: str) -> bool:
    """Verify data against a PBKDF2 hash.

    Uses constant-time comparison via hmac.compare_digest to prevent timing attacks.

    Args:
        data: The string to verify (password or API key)
        hash_str: The stored hash string

    Returns:
        True if the data matches the hash, False otherwise.
    """
    parsed = parse_pbkdf2_hash(hash_str)
    if not parsed:
        return False

    algorithm, iterations, salt, expected_hash = parsed

    computed_hash = hashlib.pbkdf2_hmac(
        algorithm,
        data.encode('utf-8'),
        salt,
        iterations
    )

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed_hash, expected_hash)

