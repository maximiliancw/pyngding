"""Web middleware: authentication decorators and utilities."""
import functools
import time

from bottle import abort, request, response

from pyngding.core.config import Config
from pyngding.web.auth import check_basic_auth


class AuthMiddleware:
    """Authentication middleware that can be shared across route modules."""
    
    def __init__(self, config: Config, db_path: str):
        self.config = config
        self.db_path = db_path
    
    def check_auth(self) -> bool:
        """Check if user is authenticated (if auth is enabled).
        
        Returns True if authenticated, raises 401 if not.
        """
        if not self.config.auth_enabled:
            return True  # No auth required

        auth_header = request.headers.get('Authorization')
        if check_basic_auth(auth_header, self.config.auth_username, self.config.auth_password_hash):
            return True

        # Request authentication
        response.status = 401
        response.headers['WWW-Authenticate'] = f'Basic realm="{self.config.auth_realm}"'
        abort(401, 'Authentication required')
    
    def require_auth(self, func):
        """Decorator to require authentication if enabled."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.config.auth_enabled:
                self.check_auth()
            return func(*args, **kwargs)
        return wrapper
    
    def require_admin(self, func):
        """Decorator to require admin access (auth must be enabled and user authenticated)."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.config.auth_enabled:
                abort(404, 'Not found')
            self.check_auth()
            return func(*args, **kwargs)
        return wrapper
    
    def check_api_key(self) -> bool:
        """Check if request has valid API key.
        
        Returns True if valid API key, False otherwise.
        """
        if not self.config.auth_enabled:
            return False

        from pyngding.core.db import get_ui_setting
        
        # Check if API is enabled
        api_enabled = get_ui_setting(self.db_path, 'api_enabled', 'true').lower() == 'true'
        if not api_enabled:
            return False

        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return False

        # Get key prefix (first 8 chars)
        if len(api_key) < 8:
            return False

        key_prefix = api_key[:8]

        # Look up key in database
        from pyngding.core.db import get_api_key_by_prefix, update_api_key_last_used
        from pyngding.web.api_keys import verify_api_key

        key_record = get_api_key_by_prefix(self.db_path, key_prefix)
        if not key_record:
            return False

        # Verify the full key
        if not verify_api_key(api_key, key_record['key_hash']):
            return False

        # Update last used timestamp
        update_api_key_last_used(self.db_path, key_record['id'], now_ts=int(time.time()))

        return True
    
    def require_api_key(self, func):
        """Decorator to require a valid API key."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.check_api_key():
                response.status = 401
                return {'error': 'Invalid or missing API key'}
            return func(*args, **kwargs)
        return wrapper

