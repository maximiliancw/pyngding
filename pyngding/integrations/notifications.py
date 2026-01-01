"""Notification system: webhook + HA webhook + ntfy."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque


class NotificationQueue:
    """Queue for notifications with rate limiting and deduplication."""

    def __init__(self, dedup_window_seconds: int = 600):
        self.dedup_window = dedup_window_seconds
        self.recent_events = deque()  # (event_type, ip, timestamp)
        self.rate_limit = {}  # channel -> last_sent_time

    def should_send(self, event_type: str, ip: str, channel: str, min_interval: int = 60) -> bool:
        """Check if event should be sent (deduplication + rate limiting)."""
        now = int(time.time())

        # Deduplication: same event type + IP within window
        cutoff = now - self.dedup_window
        while self.recent_events and self.recent_events[0][2] < cutoff:
            self.recent_events.popleft()

        for etype, eip, ets in self.recent_events:
            if etype == event_type and eip == ip and (now - ets) < self.dedup_window:
                return False  # Duplicate

        # Rate limiting per channel
        last_sent = self.rate_limit.get(channel, 0)
        if (now - last_sent) < min_interval:
            return False

        # Record event
        self.recent_events.append((event_type, ip, now))
        self.rate_limit[channel] = now

        return True


def send_webhook(url: str, payload: dict, secret: str | None = None, timeout: int = 3) -> bool:
    """Send notification to generic webhook."""
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

        if secret:
            req.add_header('X-Webhook-Secret', secret)

        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False


def send_ha_webhook(url: str, payload: dict, timeout: int = 3) -> bool:
    """Send notification to Home Assistant webhook."""
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 201)
    except Exception:
        return False


def send_ntfy(base_url: str, topic: str, message: str, title: str | None = None,
              priority: int = 3, tags: list[str] | None = None,
              auth_mode: str = 'none', username: str | None = None,
              password: str | None = None, bearer_token: str | None = None,
              timeout: int = 5) -> bool:
    """Send notification via ntfy."""
    try:
        url = f"{base_url.rstrip('/')}/{topic}"
        data = message.encode('utf-8')
        req = urllib.request.Request(url, data=data)

        if title:
            req.add_header('Title', title)
        if priority:
            req.add_header('Priority', str(priority))
        if tags:
            req.add_header('Tags', ','.join(tags))

        # Auth
        if auth_mode == 'basic' and username and password:
            import base64
            creds = base64.b64encode(f"{username}:{password}".encode()).decode()
            req.add_header('Authorization', f'Basic {creds}')
        elif auth_mode == 'bearer' and bearer_token:
            req.add_header('Authorization', f'Bearer {bearer_token}')

        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in (200, 201)
    except Exception:
        return False


def create_notification_payload(event_type: str, ip: str, mac: str | None = None,
                               hostname: str | None = None, vendor: str | None = None,
                               label: str | None = None, is_safe: bool = False,
                               tags: str | None = None, extra: dict | None = None) -> dict:
    """Create notification payload."""
    payload = {
        'event_type': event_type,
        'ts': int(time.time()),
        'ip': ip,
        'mac': mac,
        'hostname': hostname,
        'vendor': vendor,
        'label': label,
        'is_safe': is_safe,
        'tags': tags.split(',') if tags else []
    }

    if extra:
        payload.update(extra)

    return payload


def send_notification(db_path: str, event_type: str, ip: str, mac: str | None = None,
                     hostname: str | None = None, vendor: str | None = None,
                     label: str | None = None, is_safe: bool = False,
                     tags: str | None = None, extra: dict | None = None) -> dict[str, bool]:
    """Send notification to all enabled channels.

    Returns dict with channel -> success status.
    """
    from pyngding.core.db import get_ui_setting
    from pyngding.web.settings import DEFAULTS

    results = {}
    queue = NotificationQueue()

    # Check if notifications are enabled
    notify_enabled = get_ui_setting(db_path, 'notify_enabled', DEFAULTS['notify_enabled']).lower() == 'true'
    if not notify_enabled:
        return results

    # Check event-specific settings
    event_enabled_key = f"notify_on_{event_type}"
    if event_enabled_key in DEFAULTS:
        event_enabled = get_ui_setting(db_path, event_enabled_key, DEFAULTS[event_enabled_key]).lower() == 'true'
        if not event_enabled:
            return results

    # Create payload
    payload = create_notification_payload(event_type, ip, mac, hostname, vendor, label, is_safe, tags, extra)

    # Webhook
    webhook_enabled = get_ui_setting(db_path, 'webhook_enabled', 'false').lower() == 'true'
    if webhook_enabled:
        webhook_url = get_ui_setting(db_path, 'webhook_url', '')
        webhook_secret = get_ui_setting(db_path, 'webhook_secret', '') or None
        timeout = int(get_ui_setting(db_path, 'webhook_timeout_seconds', '3'))

        if webhook_url and queue.should_send(event_type, ip, 'webhook'):
            results['webhook'] = send_webhook(webhook_url, payload, webhook_secret, timeout)

    # HA Webhook
    ha_webhook_enabled = get_ui_setting(db_path, 'ha_webhook_enabled', 'false').lower() == 'true'
    if ha_webhook_enabled:
        ha_webhook_url = get_ui_setting(db_path, 'ha_webhook_url', '')
        timeout = int(get_ui_setting(db_path, 'ha_webhook_timeout_seconds', '3'))

        if ha_webhook_url and queue.should_send(event_type, ip, 'ha_webhook'):
            results['ha_webhook'] = send_ha_webhook(ha_webhook_url, payload, timeout)

    # ntfy
    ntfy_enabled = get_ui_setting(db_path, 'ntfy_enabled', 'false').lower() == 'true'
    if ntfy_enabled:
        ntfy_base_url = get_ui_setting(db_path, 'ntfy_base_url', 'https://ntfy.sh')
        ntfy_topic = get_ui_setting(db_path, 'ntfy_topic', '')
        ntfy_auth_mode = get_ui_setting(db_path, 'ntfy_auth_mode', 'none')
        ntfy_username = get_ui_setting(db_path, 'ntfy_username', '') or None
        ntfy_password = get_ui_setting(db_path, 'ntfy_password', '') or None
        ntfy_bearer_token = get_ui_setting(db_path, 'ntfy_bearer_token', '') or None
        ntfy_priority = int(get_ui_setting(db_path, 'ntfy_priority', '3'))
        ntfy_tags_str = get_ui_setting(db_path, 'ntfy_tags', '')
        ntfy_tags = [t.strip() for t in ntfy_tags_str.split(',') if t.strip()] if ntfy_tags_str else None

        if ntfy_topic and queue.should_send(event_type, ip, 'ntfy'):
            title = f"pyngding: {event_type.replace('_', ' ').title()}"
            message = f"IP: {ip}"
            if hostname:
                message += f" ({hostname})"
            if label:
                message += f" - {label}"

            results['ntfy'] = send_ntfy(
                ntfy_base_url, ntfy_topic, message, title=title,
                priority=ntfy_priority, tags=ntfy_tags,
                auth_mode=ntfy_auth_mode, username=ntfy_username,
                password=ntfy_password, bearer_token=ntfy_bearer_token
            )

    return results

