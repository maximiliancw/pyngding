"""Bottle web application."""
import base64
import json
import time
from bottle import Bottle, request, response, template, static_file, abort

from pyngding.web.auth import check_basic_auth
from pyngding.core.config import Config
from pyngding.core.db import get_all_hosts, get_recent_scan_runs, get_scan_stats, get_db, get_ui_setting as db_get_ui_setting
from pyngding.scanning.scheduler import ScanScheduler


def create_app(config: Config, db_path: str, scheduler: ScanScheduler) -> Bottle:
    """Create and configure the Bottle application."""
    app = Bottle()
    
    # Template settings
    app.template_adapter = lambda template_name, **kwargs: template(
        template_name,
        template_lookup=['pyngding/templates'],
        **kwargs
    )
    
    def check_auth():
        """Check if user is authenticated (if auth is enabled)."""
        if not config.auth_enabled:
            return True  # No auth required
        
        auth_header = request.headers.get('Authorization')
        if check_basic_auth(auth_header, config.auth_username, config.auth_password_hash):
            return True
        
        # Request authentication
        response.status = 401
        response.headers['WWW-Authenticate'] = f'Basic realm="{config.auth_realm}"'
        abort(401, 'Authentication required')
    
    def require_auth_if_enabled():
        """Require auth if it's enabled in config."""
        if config.auth_enabled:
            check_auth()
    
    # Static files (no auth required)
    @app.route('/static/<filename:path>')
    def serve_static(filename):
        return static_file(filename, root='pyngding/static')
    
    # Dashboard (auth required if enabled)
    @app.route('/')
    def dashboard():
        require_auth_if_enabled()
        stats = get_scan_stats(db_path)
        chart_window = int(get_ui_setting_helper(db_path, 'chart_window_runs', '200'))
        runs = get_recent_scan_runs(db_path, limit=chart_window)
        
        # Get new/unsafe hosts for quick actions
        from pyngding.core.db import get_hosts_with_profiles
        all_hosts = get_hosts_with_profiles(db_path)
        new_hosts = [h for h in all_hosts if h.get('profile_is_safe') != 1 and h['last_status'] == 'up']
        
        # Get IPv6 neighbor count (last hour)
        ipv6_enabled = get_ui_setting_helper(db_path, 'ipv6_passive_enabled', 'true').lower() == 'true'
        ipv6_count = 0
        if ipv6_enabled:
            from pyngding.scanning.ipv6 import get_recent_ipv6_neighbors
            ipv6_neighbors = get_recent_ipv6_neighbors(db_path, hours=1)
            ipv6_count = len(ipv6_neighbors)
        
        # Prepare chart data (reverse for chronological order)
        chart_data = {
            'labels': [f"Run {r['id']}" for r in reversed(runs)],
            'up_counts': [r['up_count'] for r in reversed(runs)]
        }
        chart_data_json = json.dumps(chart_data)
        
        return template('dashboard.tpl', stats=stats, chart_data_json=chart_data_json, 
                       auth_enabled=config.auth_enabled, new_hosts=new_hosts[:10],
                       ipv6_enabled=ipv6_enabled, ipv6_count=ipv6_count)
    
    # Hosts page (auth required if enabled)
    @app.route('/hosts')
    def hosts():
        require_auth_if_enabled()
        status_filter = request.query.get('status', '').strip()
        search = request.query.get('search', '').strip().lower()
        
        all_hosts = get_all_hosts(db_path, status=status_filter if status_filter else None)
        
        # Apply search filter
        if search:
            filtered = []
            for host in all_hosts:
                if (search in host['ip'].lower() or
                    (host['hostname'] and search in host['hostname'].lower()) or
                    (host['mac'] and search in host['mac'].lower()) or
                    (host['vendor'] and search in host['vendor'].lower())):
                    filtered.append(host)
            all_hosts = filtered
        
        return template('hosts.tpl', hosts=all_hosts, status_filter=status_filter, search=search, auth_enabled=config.auth_enabled)
    
    # HTMX partials (auth required if enabled)
    @app.route('/partials/summary')
    def partials_summary():
        require_auth_if_enabled()
        stats = get_scan_stats(db_path)
        return template('partials/summary.tpl', stats=stats)
    
    @app.route('/partials/recent-changes')
    def partials_recent_changes():
        require_auth_if_enabled()
        # Get recent scan runs
        recent_runs = get_recent_scan_runs(db_path, limit=10)
        return template('partials/recent-changes.tpl', runs=recent_runs)
    
    @app.route('/partials/hosts-table')
    def partials_hosts_table():
        require_auth_if_enabled()
        status_filter = request.query.get('status', '').strip()
        search = request.query.get('search', '').strip().lower()
        
        all_hosts = get_all_hosts(db_path, status=status_filter if status_filter else None)
        
        if search:
            filtered = []
            for host in all_hosts:
                if (search in host['ip'].lower() or
                    (host['hostname'] and search in host['hostname'].lower()) or
                    (host['mac'] and search in host['mac'].lower()) or
                    (host['vendor'] and search in host['vendor'].lower())):
                    filtered.append(host)
            all_hosts = filtered
        
        return template('partials/hosts-table.tpl', hosts=all_hosts)
    
    @app.route('/partials/dns-host/<ip>')
    def partials_dns_host(ip):
        require_auth_if_enabled()
        
        from pyngding.core.db import get_host_dns_summary
        from pyngding.web.settings import DEFAULTS
        
        adguard_enabled = get_ui_setting_helper(db_path, 'adguard_enabled', DEFAULTS['adguard_enabled']).lower() == 'true'
        if not adguard_enabled:
            return template('partials/dns-host.tpl', enabled=False, ip=ip)
        
        summary = get_host_dns_summary(db_path, ip, limit=20)
        return template('partials/dns-host.tpl', enabled=True, ip=ip, summary=summary)
    
    # Admin routes (only accessible when auth is enabled)
    @app.route('/admin/settings')
    def admin_settings():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.web.settings import get_all_settings
        settings = get_all_settings(db_path)
        return template('admin_settings.tpl', settings=settings, auth_enabled=True)
    
    @app.route('/admin/settings', method='POST')
    def admin_settings_update():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.web.settings import validate_setting, sanitize_setting, DEFAULTS
        from pyngding.core.db import set_ui_setting
        
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
            from pyngding.web.settings import get_all_settings
            settings = get_all_settings(db_path)
            return template('admin_settings.tpl', settings=settings, auth_enabled=True, 
                          errors=errors, updated=updated)
        
        # Redirect to show success
        response.status = 303
        response.headers['Location'] = '/admin/settings?updated=' + ','.join(updated)
        return ''
    
    @app.route('/admin/hosts')
    def admin_hosts():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.core.db import get_hosts_with_profiles
        hosts = get_hosts_with_profiles(db_path)
        return template('admin_hosts.tpl', hosts=hosts, auth_enabled=True)
    
    @app.route('/admin/hosts/<host_ip>/update', method='POST')
    def admin_hosts_update(host_ip):
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.core.db import get_host, upsert_device_profile
        import time
        
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
        
        # Redirect back to admin hosts page
        response.status = 303
        response.headers['Location'] = '/admin/hosts'
        return ''
    
    @app.route('/admin/api-keys')
    def admin_api_keys():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.core.db import get_all_api_keys
        api_keys = get_all_api_keys(db_path)
        return template('admin_api_keys.tpl', api_keys=api_keys, auth_enabled=True, new_key=None)
    
    @app.route('/admin/api-keys', method='POST')
    def admin_api_keys_create():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.web.api_keys import generate_api_key, hash_api_key
        from pyngding.core.db import create_api_key, get_all_api_keys
        import time
        
        name = request.forms.get('name', '').strip()
        if not name:
            api_keys = get_all_api_keys(db_path)
            return template('admin_api_keys.tpl', api_keys=api_keys, auth_enabled=True, 
                          new_key=None, error='Name is required')
        
        # Generate key
        full_key, key_prefix = generate_api_key()
        key_hash = hash_api_key(full_key)
        
        # Store in DB
        create_api_key(db_path, name, key_prefix, key_hash, now_ts=int(time.time()))
        
        # Show key once
        api_keys = get_all_api_keys(db_path)
        return template('admin_api_keys.tpl', api_keys=api_keys, auth_enabled=True, 
                       new_key={'name': name, 'key': full_key, 'prefix': key_prefix})
    
    @app.route('/admin/api-keys/<key_id>/toggle', method='POST')
    def admin_api_keys_toggle(key_id):
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.core.db import get_all_api_keys, toggle_api_key
        
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
    def admin_api_keys_delete(key_id):
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.core.db import delete_api_key
        
        try:
            key_id_int = int(key_id)
            delete_api_key(db_path, key_id_int)
            
            response.status = 303
            response.headers['Location'] = '/admin/api-keys'
            return ''
        except ValueError:
            abort(404, 'Invalid key ID')
    
    @app.route('/admin/adguard')
    def admin_adguard():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.core.db import get_adguard_state, get_db
        from pyngding.web.settings import DEFAULTS
        
        adguard_enabled = get_ui_setting_helper(db_path, 'adguard_enabled', DEFAULTS['adguard_enabled']).lower() == 'true'
        state = get_adguard_state(db_path)
        
        # Get event counts
        with get_db(db_path) as conn:
            total_events = conn.execute("SELECT COUNT(*) FROM dns_events").fetchone()[0]
            recent_events = conn.execute("""
                SELECT COUNT(*) FROM dns_events WHERE ts >= ?
            """, (int(time.time()) - 3600,)).fetchone()[0]
        
        return template('admin_adguard.tpl', 
                       adguard_enabled=adguard_enabled,
                       state=state,
                       total_events=total_events,
                       recent_events=recent_events,
                       auth_enabled=True)
    
    @app.route('/admin/ipv6')
    def admin_ipv6():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
        from pyngding.scanning.ipv6 import get_recent_ipv6_neighbors
        from pyngding.web.settings import DEFAULTS
        
        ipv6_enabled = get_ui_setting_helper(db_path, 'ipv6_passive_enabled', DEFAULTS['ipv6_passive_enabled']).lower() == 'true'
        
        # Get recent neighbors (last 24 hours)
        neighbors_24h = get_recent_ipv6_neighbors(db_path, hours=24)
        
        return template('admin_ipv6.tpl',
                       ipv6_enabled=ipv6_enabled,
                       neighbors=neighbors_24h,
                       auth_enabled=True)
    
    @app.route('/admin/<path:path>')
    def admin_404(path):
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()  # Require auth for admin routes
        abort(404, 'Admin route not yet implemented')
    
    def check_api_key():
        """Check if request has valid API key."""
        if not config.auth_enabled:
            return False
        
        # Check if API is enabled
        api_enabled = get_ui_setting_helper(db_path, 'api_enabled', 'true').lower() == 'true'
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
        from pyngding.core.db import get_api_key_by_prefix
        from pyngding.web.api_keys import verify_api_key
        import time
        
        key_record = get_api_key_by_prefix(db_path, key_prefix)
        if not key_record:
            return False
        
        # Verify the full key
        if not verify_api_key(api_key, key_record['key_hash']):
            return False
        
        # Update last used timestamp
        from pyngding.core.db import update_api_key_last_used
        update_api_key_last_used(db_path, key_record['id'], now_ts=int(time.time()))
        
        return True
    
    # API routes (only accessible when auth is enabled AND api_enabled)
    @app.route('/api/health')
    def api_health():
        if not check_api_key():
            response.status = 401
            return {'error': 'Invalid or missing API key'}
        return {'status': 'ok'}
    
    @app.route('/api/ha/summary')
    def api_ha_summary():
        if not check_api_key():
            response.status = 401
            return {'error': 'Invalid or missing API key'}
        
        stats = get_scan_stats(db_path)
        return {
            'up_count': stats.get('up_count', 0),
            'down_count': stats.get('down_count', 0),
            'total_hosts': stats.get('total_hosts', 0),
            'missing_count': stats.get('missing_count', 0),
            'last_scan_ts': stats.get('last_scan_ts')
        }
    
    @app.route('/api/ha/hosts')
    def api_ha_hosts():
        if not check_api_key():
            response.status = 401
            return {'error': 'Invalid or missing API key'}
        
        status_filter = request.query.get('status', '').strip().lower()
        if status_filter not in ('up', 'down', ''):
            status_filter = ''
        
        from pyngding.core.db import get_hosts_with_profiles
        hosts = get_hosts_with_profiles(db_path)
        
        # Filter by status if requested
        if status_filter:
            hosts = [h for h in hosts if h['last_status'] == status_filter]
        
        # Format for HA
        result = []
        for host in hosts:
            result.append({
                'ip': host['ip'],
                'hostname': host.get('hostname'),
                'mac': host.get('mac'),
                'vendor': host.get('vendor'),
                'status': host['last_status'],
                'rtt_ms': host.get('last_rtt_ms'),
                'first_seen_ts': host['first_seen_ts'],
                'last_seen_ts': host['last_seen_ts'],
                'label': host.get('profile_label'),
                'is_safe': bool(host.get('profile_is_safe')),
                'tags': host.get('profile_tags', '').split(',') if host.get('profile_tags') else []
            })
        
        return {'hosts': result}
    
    @app.route('/api/ha/alerts/recent')
    def api_ha_alerts_recent():
        if not check_api_key():
            response.status = 401
            return {'error': 'Invalid or missing API key'}
        
        limit = int(request.query.get('limit', '10'))
        if limit > 100:
            limit = 100
        
        # For now, return empty list - alerts will be implemented with notifications
        # This is a placeholder for future enhancement
        return {'alerts': []}
    
    @app.route('/api/<path:path>')
    def api_404(path):
        if not config.auth_enabled:
            abort(404, 'Not found')
        if not check_api_key():
            response.status = 401
            return {'error': 'Invalid or missing API key'}
        abort(404, 'API route not found')
    
    # Metrics endpoint (only when auth enabled AND metrics_enabled)
    @app.route('/metrics')
    def metrics():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()  # Require auth for metrics
        
        metrics_enabled = get_ui_setting_helper(db_path, 'metrics_enabled', 'true').lower() == 'true'
        if not metrics_enabled:
            abort(404, 'Metrics disabled')
        
        from pyngding.core.db import get_db
        from pyngding.scanning.scheduler import get_scan_stats
        
        stats = get_scan_stats(db_path)
        
        # Get scan run stats
        with get_db(db_path) as conn:
            total_runs = conn.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0] or 0
            total_observations = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0] or 0
            total_dns_events = conn.execute("SELECT COUNT(*) FROM dns_events").fetchone()[0] or 0
        
        # Prometheus text format
        response.content_type = 'text/plain; version=0.0.4'
        
        metrics_text = f"""# HELP pyngding_hosts_up Number of hosts currently up
# TYPE pyngding_hosts_up gauge
pyngding_hosts_up {stats.get('up_count', 0)}

# HELP pyngding_hosts_down Number of hosts currently down
# TYPE pyngding_hosts_down gauge
pyngding_hosts_down {stats.get('down_count', 0)}

# HELP pyngding_hosts_total Total number of hosts
# TYPE pyngding_hosts_total gauge
pyngding_hosts_total {stats.get('total_hosts', 0)}

# HELP pyngding_hosts_missing Number of missing hosts
# TYPE pyngding_hosts_missing gauge
pyngding_hosts_missing {stats.get('missing_count', 0)}

# HELP pyngding_scan_runs_total Total number of scan runs
# TYPE pyngding_scan_runs_total counter
pyngding_scan_runs_total {total_runs}

# HELP pyngding_observations_total Total number of observations
# TYPE pyngding_observations_total counter
pyngding_observations_total {total_observations}

# HELP pyngding_dns_events_total Total number of DNS events
# TYPE pyngding_dns_events_total counter
pyngding_dns_events_total {total_dns_events}

# HELP pyngding_last_scan_timestamp Timestamp of last scan
# TYPE pyngding_last_scan_timestamp gauge
pyngding_last_scan_timestamp {stats.get('last_scan_ts', 0)}
"""
        
        return metrics_text
    
    # Admin notification test
    @app.route('/admin/notify/test', method='POST')
    def admin_notify_test():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()
        
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
    
    return app


def get_ui_setting_helper(db_path: str, key: str, default: str) -> str:
    """Helper to get UI setting."""
    return db_get_ui_setting(db_path, key, default)

