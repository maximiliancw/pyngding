"""Admin routes (settings, hosts, API keys, AdGuard, IPv6)."""
import time

from bottle import abort, request, response

from pyngding.core.db import (
    create_api_key,
    delete_api_key,
    get_adguard_state,
    get_all_api_keys,
    get_db,
    get_host,
    get_hosts_with_profiles,
    set_ui_setting,
    toggle_api_key,
    upsert_device_profile,
)
from pyngding.core.db import get_ui_setting as db_get_ui_setting
from pyngding.web.api_keys import generate_api_key, hash_api_key
from pyngding.web.middleware import AuthMiddleware
from pyngding.web.settings import DEFAULTS, get_all_settings, sanitize_setting, validate_setting


def register_routes(app, auth: AuthMiddleware, db_path: str, render_template):
    """Register admin routes on the app."""
    
    def get_ui_setting_helper(key: str, default: str) -> str:
        return db_get_ui_setting(db_path, key, default)

    # Settings
    @app.route('/admin/settings')
    @auth.require_admin
    def admin_settings():
        settings = get_all_settings(db_path)
        return render_template('admin_settings.tpl', settings=settings, auth_enabled=True)

    @app.route('/admin/settings', method='POST')
    @auth.require_admin
    def admin_settings_update():
        errors = []
        updated = []

        for key in DEFAULTS.keys():
            if key in request.forms:
                value = request.forms.get(key, '').strip()
                # Use default if empty for optional fields
                if not value and key not in ('webhook_url', 'ha_webhook_url', 'ntfy_topic',
                                            'adguard_base_url', 'adguard_querylog_path',
                                            'oui_file_path'):
                    value = DEFAULTS[key]

                # Validate
                is_valid, error_msg = validate_setting(key, value)
                if not is_valid:
                    errors.append(f"{key}: {error_msg}")
                    continue

                # Sanitize and save
                sanitized = sanitize_setting(key, value)
                set_ui_setting(db_path, key, sanitized)
                updated.append(key)

        if errors:
            settings = get_all_settings(db_path)
            return render_template('admin_settings.tpl', settings=settings, auth_enabled=True,
                                    errors=errors, updated=updated)

        # Redirect to show success
        response.status = 303
        response.headers['Location'] = '/admin/settings?updated=' + ','.join(updated)
        return ''

    # Hosts management
    @app.route('/admin/hosts')
    @auth.require_admin
    def admin_hosts():
        hosts = get_hosts_with_profiles(db_path)
        return render_template('admin_hosts.tpl', hosts=hosts, auth_enabled=True)

    @app.route('/admin/hosts/<host_ip>/update', method='POST')
    @auth.require_admin
    def admin_hosts_update(host_ip):
        host = get_host(db_path, host_ip)
        if not host:
            abort(404, 'Host not found')

        label = request.forms.get('label', '').strip() or None
        is_safe = request.forms.get('is_safe', '').lower() == 'true'
        tags = request.forms.get('tags', '').strip() or None
        notes = request.forms.get('notes', '').strip() or None

        upsert_device_profile(
            db_path,
            mac=host.get('mac'),
            ip=host['ip'],
            label=label,
            is_safe=is_safe,
            tags=tags,
            notes=notes,
            now_ts=int(time.time())
        )

        response.status = 303
        response.headers['Location'] = '/admin/hosts'
        return ''

    # API Keys
    @app.route('/admin/api-keys')
    @auth.require_admin
    def admin_api_keys():
        api_keys = get_all_api_keys(db_path)
        return render_template('admin_api_keys.tpl', api_keys=api_keys, auth_enabled=True, new_key=None)

    @app.route('/admin/api-keys', method='POST')
    @auth.require_admin
    def admin_api_keys_create():
        name = request.forms.get('name', '').strip()
        if not name:
            api_keys = get_all_api_keys(db_path)
            return render_template('admin_api_keys.tpl', api_keys=api_keys, auth_enabled=True,
                                    new_key=None, error='Name is required')

        # Generate key
        full_key, key_prefix = generate_api_key()
        key_hash = hash_api_key(full_key)

        # Store in DB
        create_api_key(db_path, name, key_prefix, key_hash, now_ts=int(time.time()))

        # Show key once
        api_keys = get_all_api_keys(db_path)
        return render_template('admin_api_keys.tpl', api_keys=api_keys, auth_enabled=True,
                                new_key={'name': name, 'key': full_key, 'prefix': key_prefix})

    @app.route('/admin/api-keys/<key_id>/toggle', method='POST')
    @auth.require_admin
    def admin_api_keys_toggle(key_id):
        try:
            key_id_int = int(key_id)
            # Get current state
            all_keys = get_all_api_keys(db_path)
            key = next((k for k in all_keys if k['id'] == key_id_int), None)
            if not key:
                abort(404, 'API key not found')

            # Toggle
            toggle_api_key(db_path, key_id_int, not key['is_enabled'])

            response.status = 303
            response.headers['Location'] = '/admin/api-keys'
            return ''
        except ValueError:
            abort(404, 'Invalid key ID')

    @app.route('/admin/api-keys/<key_id>/delete', method='POST')
    @auth.require_admin
    def admin_api_keys_delete(key_id):
        try:
            key_id_int = int(key_id)
            delete_api_key(db_path, key_id_int)

            response.status = 303
            response.headers['Location'] = '/admin/api-keys'
            return ''
        except ValueError:
            abort(404, 'Invalid key ID')

    # AdGuard
    @app.route('/admin/adguard')
    @auth.require_admin
    def admin_adguard():
        adguard_enabled = get_ui_setting_helper('adguard_enabled', DEFAULTS['adguard_enabled']).lower() == 'true'
        state = get_adguard_state(db_path)

        # Get event counts
        with get_db(db_path) as conn:
            total_events = conn.execute("SELECT COUNT(*) FROM dns_events").fetchone()[0]
            recent_events = conn.execute("""
                SELECT COUNT(*) FROM dns_events WHERE ts >= ?
            """, (int(time.time()) - 3600,)).fetchone()[0]

        return render_template('admin_adguard.tpl',
                                adguard_enabled=adguard_enabled,
                                state=state,
                                total_events=total_events,
                                recent_events=recent_events,
                                auth_enabled=True)

    # IPv6
    @app.route('/admin/ipv6')
    @auth.require_admin
    def admin_ipv6():
        from pyngding.scanning.ipv6 import get_recent_ipv6_neighbors

        ipv6_enabled = get_ui_setting_helper('ipv6_passive_enabled', DEFAULTS['ipv6_passive_enabled']).lower() == 'true'

        # Get recent neighbors (last 24 hours)
        neighbors_24h = get_recent_ipv6_neighbors(db_path, hours=24)

        return render_template('admin_ipv6.tpl',
                                ipv6_enabled=ipv6_enabled,
                                neighbors=neighbors_24h,
                                auth_enabled=True)

    # Notification test
    @app.route('/admin/notify/test', method='POST')
    @auth.require_admin
    def admin_notify_test():
        from pyngding.integrations.notifications import send_notification

        channel = request.forms.get('channel', 'webhook')
        test_ip = request.forms.get('ip', '192.168.1.100')

        # Send test notification
        results = send_notification(
            db_path,
            event_type='test',
            ip=test_ip,
            hostname='Test Device',
            label='Test Notification',
            extra={'test': True}
        )

        if channel in results:
            success = results[channel]
            response.status = 303
            response.headers['Location'] = f'/admin/settings?notify_test={channel}&success={success}'
        else:
            response.status = 303
            response.headers['Location'] = f'/admin/settings?notify_test={channel}&success=false'
        return ''

    # Catch-all for admin routes
    @app.route('/admin/<path:path>')
    @auth.require_admin
    def admin_404(path):
        abort(404, 'Admin route not yet implemented')

