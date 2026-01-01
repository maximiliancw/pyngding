"""UI settings defaults and validation with TTL caching."""
import threading
import time
from typing import Any

# Settings cache with TTL
_settings_cache: dict[str, tuple[str, float]] = {}  # key -> (value, expiry_ts)
_cache_lock = threading.Lock()
CACHE_TTL = 30  # seconds before cached settings expire

# Default values for UI settings
DEFAULTS: dict[str, Any] = {
    'reverse_dns': 'true',
    'missing_threshold_minutes': '10',
    'chart_window_runs': '200',
    'ui_refresh_seconds': '10',
    'metrics_enabled': 'true',
    'api_enabled': 'true',
    'api_rate_limit_rps': '5',
    'raw_observation_retention_days': '90',
    'dns_event_retention_days': '7',
    'scan_run_retention_days': '365',
    'adguard_enabled': 'false',
    'adguard_mode': 'api',
    'adguard_base_url': '',
    'adguard_username': '',
    'adguard_password': '',
    'adguard_querylog_path': '',
    'adguard_ingest_interval_seconds': '30',
    'adguard_max_fetch': '500',
    'notify_enabled': 'true',
    'notify_on_new_host': 'true',
    'notify_on_host_gone': 'true',
    'notify_on_ip_mac_change': 'true',
    'notify_on_duplicate_ip': 'true',
    'notify_on_dns_burst': 'false',
    'webhook_enabled': 'false',
    'webhook_url': '',
    'webhook_secret': '',
    'webhook_timeout_seconds': '3',
    'ha_webhook_enabled': 'false',
    'ha_webhook_url': '',
    'ha_webhook_timeout_seconds': '3',
    'ntfy_enabled': 'false',
    'ntfy_base_url': 'https://ntfy.sh',
    'ntfy_topic': '',
    'ntfy_auth_mode': 'none',
    'ntfy_username': '',
    'ntfy_password': '',
    'ntfy_bearer_token': '',
    'ntfy_priority': '3',
    'ntfy_tags': '',
    'ipv6_passive_enabled': 'true',
    'oui_lookup_enabled': 'false',
    'oui_file_path': '',
}


def validate_setting(key: str, value: str) -> tuple[bool, str | None]:
    """Validate a setting value. Returns (is_valid, error_message)."""
    # Boolean settings
    if key.endswith('_enabled') or key.startswith('notify_on_'):
        if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
            return False, f"Invalid boolean value for {key}"
        return True, None

    # Integer settings
    if key.endswith('_seconds') or key.endswith('_minutes') or key.endswith('_days') or \
       key.endswith('_rps') or key.endswith('_runs') or key.endswith('_fetch') or \
       key.endswith('_priority') or key.endswith('_timeout_seconds'):
        try:
            int_val = int(value)
            if int_val < 0:
                return False, f"{key} must be non-negative"
            # Specific validations
            if key == 'api_rate_limit_rps' and int_val > 100:
                return False, "API rate limit too high (max 100)"
            if key == 'chart_window_runs' and int_val > 1000:
                return False, "Chart window too large (max 1000)"
            return True, None
        except ValueError:
            return False, f"{key} must be an integer"

    # URL settings
    if key.endswith('_url') and value:
        if not (value.startswith('http://') or value.startswith('https://')):
            return False, f"{key} must be a valid URL starting with http:// or https://"

    # String settings - basic sanitization
    if len(value) > 1000:
        return False, f"{key} value too long (max 1000 characters)"

    return True, None


def sanitize_setting(key: str, value: str) -> str:
    """Sanitize a setting value."""
    # Strip whitespace
    value = value.strip()

    # Normalize boolean values
    if key.endswith('_enabled') or key.startswith('notify_on_'):
        if value.lower() in ('true', '1', 'yes', 'on'):
            return 'true'
        elif value.lower() in ('false', '0', 'no', 'off'):
            return 'false'

    return value


def get_cached_setting(db_path: str, key: str, default: str | None = None) -> str | None:
    """Get a UI setting with TTL caching.
    
    Settings are cached for CACHE_TTL seconds to reduce database reads.
    Thread-safe for concurrent access.
    
    Args:
        db_path: Path to the database
        key: Setting key
        default: Default value if not found
    
    Returns:
        The setting value or default.
    """
    from pyngding.core.db import get_ui_setting
    
    now = time.time()
    cache_key = f"{db_path}:{key}"
    
    # Check cache first (with lock for thread safety)
    with _cache_lock:
        if cache_key in _settings_cache:
            value, expiry = _settings_cache[cache_key]
            if now < expiry:
                return value
            # Expired - remove from cache
            del _settings_cache[cache_key]
    
    # Fetch from database
    value = get_ui_setting(db_path, key, default)
    
    # Cache the result
    with _cache_lock:
        _settings_cache[cache_key] = (value, now + CACHE_TTL)
    
    return value


def invalidate_settings_cache(db_path: str | None = None, key: str | None = None) -> int:
    """Invalidate settings cache.
    
    Args:
        db_path: If provided, only invalidate settings for this db_path
        key: If provided, only invalidate this specific key
    
    Returns:
        Number of cache entries invalidated.
    """
    with _cache_lock:
        if db_path is None and key is None:
            # Clear all
            count = len(_settings_cache)
            _settings_cache.clear()
            return count
        
        # Selective invalidation
        to_delete = []
        for cache_key in _settings_cache:
            if db_path and not cache_key.startswith(f"{db_path}:"):
                continue
            if key and not cache_key.endswith(f":{key}"):
                continue
            to_delete.append(cache_key)
        
        for k in to_delete:
            del _settings_cache[k]
        
        return len(to_delete)


def get_all_settings(db_path: str) -> dict[str, str]:
    """Get all UI settings with defaults.
    
    Uses cached settings where available.
    """
    settings = {}
    for key, default in DEFAULTS.items():
        settings[key] = get_cached_setting(db_path, key, default)

    return settings

