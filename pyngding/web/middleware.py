"""Web middleware: authentication decorators and utilities."""
import functools
import threading
import time

from bottle import abort, request, response

from pyngding.core.config import Config
from pyngding.web.auth import check_basic_auth


class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter.
    
    Each client (identified by API key prefix) gets a bucket that refills at
    the configured rate. Requests consume tokens; if no tokens available,
    the request is rate-limited.
    """
    
    def __init__(self, default_rate: float = 5.0, bucket_size: int = 10):
        """Initialize the rate limiter.
        
        Args:
            default_rate: Tokens per second to refill
            bucket_size: Maximum tokens in bucket
        """
        self.default_rate = default_rate
        self.bucket_size = bucket_size
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, last_update_ts)
        self._lock = threading.Lock()
    
    def allow_request(self, client_id: str, rate: float | None = None) -> tuple[bool, float]:
        """Check if a request is allowed under rate limiting.
        
        Args:
            client_id: Unique identifier for the client (e.g., API key prefix)
            rate: Override rate for this check (tokens/second)
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        now = time.time()
        effective_rate = rate if rate is not None else self.default_rate
        
        with self._lock:
            if client_id in self._buckets:
                tokens, last_update = self._buckets[client_id]
            else:
                tokens, last_update = self.bucket_size, now
            
            # Refill tokens based on elapsed time
            elapsed = now - last_update
            tokens = min(self.bucket_size, tokens + elapsed * effective_rate)
            
            if tokens >= 1.0:
                # Allow request, consume a token
                self._buckets[client_id] = (tokens - 1.0, now)
                return True, 0.0
            else:
                # Rate limited - calculate retry time
                self._buckets[client_id] = (tokens, now)
                tokens_needed = 1.0 - tokens
                retry_after = tokens_needed / effective_rate if effective_rate > 0 else 60.0
                return False, retry_after
    
    def cleanup_old_buckets(self, max_age_seconds: float = 3600) -> int:
        """Remove buckets that haven't been used recently.
        
        Returns number of buckets removed.
        """
        now = time.time()
        cutoff = now - max_age_seconds
        
        with self._lock:
            to_remove = [k for k, (_, ts) in self._buckets.items() if ts < cutoff]
            for k in to_remove:
                del self._buckets[k]
            return len(to_remove)


# Global rate limiter instance
_api_rate_limiter = TokenBucketRateLimiter()


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
    
    def check_rate_limit(self, client_id: str) -> tuple[bool, float]:
        """Check if request is within rate limit.
        
        Args:
            client_id: Client identifier (API key prefix)
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        from pyngding.web.settings import get_cached_setting
        
        # Get configured rate limit
        rate_str = get_cached_setting(self.db_path, 'api_rate_limit_rps', '5')
        try:
            rate = float(rate_str)
        except (ValueError, TypeError):
            rate = 5.0
        
        return _api_rate_limiter.allow_request(client_id, rate)
    
    def require_api_key(self, func):
        """Decorator to require a valid API key with rate limiting."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.check_api_key():
                response.status = 401
                return {'error': 'Invalid or missing API key'}
            
            # Apply rate limiting based on API key prefix
            api_key = request.headers.get('X-API-Key', '')
            client_id = api_key[:8] if len(api_key) >= 8 else 'unknown'
            
            allowed, retry_after = self.check_rate_limit(client_id)
            if not allowed:
                response.status = 429
                response.headers['Retry-After'] = str(int(retry_after) + 1)
                return {'error': 'Rate limit exceeded', 'retry_after': retry_after}
            
            return func(*args, **kwargs)
        return wrapper

