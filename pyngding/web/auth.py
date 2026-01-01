"""BasicAuth implementation using shared PBKDF2 utilities."""
import base64

from pyngding.core.crypto import verify_pbkdf2


def check_basic_auth(auth_header: str | None, username: str, password_hash: str) -> bool:
    """Check BasicAuth header against credentials.

    Args:
        auth_header: The Authorization header value
        username: Expected username
        password_hash: PBKDF2 hash of the expected password

    Returns:
        True if authentication succeeds, False otherwise.
    """
    if not auth_header:
        return False

    if not auth_header.startswith('Basic '):
        return False

    try:
        encoded = auth_header[6:]  # Remove "Basic " prefix
        decoded = base64.b64decode(encoded).decode('utf-8')
        user, password = decoded.split(':', 1)

        if user != username:
            return False

        return verify_pbkdf2(password, password_hash)
    except Exception:
        return False
