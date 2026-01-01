"""API routes for external integrations (Home Assistant, etc.)."""
from bottle import abort, request, response

from pyngding.core.db import get_db, get_hosts_with_profiles
from pyngding.core.db import get_ui_setting as db_get_ui_setting
from pyngding.scanning.scheduler import get_scan_stats
from pyngding.web.middleware import AuthMiddleware


def register_routes(app, auth: AuthMiddleware, db_path: str):
    """Register API routes on the app."""

    @app.route('/api/health')
    @auth.require_api_key
    def api_health():
        return {'status': 'ok'}

    @app.route('/api/ha/summary')
    @auth.require_api_key
    def api_ha_summary():
        stats = get_scan_stats(db_path)
        return {
            'up_count': stats.get('up_count', 0),
            'down_count': stats.get('down_count', 0),
            'total_hosts': stats.get('total_hosts', 0),
            'missing_count': stats.get('missing_count', 0),
            'last_scan_ts': stats.get('last_scan_ts')
        }

    @app.route('/api/ha/hosts')
    @auth.require_api_key
    def api_ha_hosts():
        status_filter = request.query.get('status', '').strip().lower()
        if status_filter not in ('up', 'down', ''):
            status_filter = ''

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
    @auth.require_api_key
    def api_ha_alerts_recent():
        limit = int(request.query.get('limit', '10'))
        if limit > 100:
            limit = 100

        # For now, return empty list - alerts will be implemented with notifications
        # This is a placeholder for future enhancement
        return {'alerts': []}

    @app.route('/api/<path:path>')
    def api_404(path):
        if not auth.config.auth_enabled:
            abort(404, 'Not found')
        if not auth.check_api_key():
            response.status = 401
            return {'error': 'Invalid or missing API key'}
        abort(404, 'API route not found')

