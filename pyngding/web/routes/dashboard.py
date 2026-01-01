"""Dashboard and HTMX partial routes."""
import json

from pyngding.core.db import get_all_hosts, get_hosts_with_profiles, get_recent_scan_runs
from pyngding.core.db import get_ui_setting as db_get_ui_setting
from pyngding.scanning.scheduler import get_scan_stats
from pyngding.web.middleware import AuthMiddleware


def register_routes(app, auth: AuthMiddleware, db_path: str, render_template):
    """Register dashboard routes on the app."""
    
    def get_ui_setting_helper(key: str, default: str) -> str:
        return db_get_ui_setting(db_path, key, default)

    @app.route('/')
    @auth.require_auth
    def dashboard():
        stats = get_scan_stats(db_path)
        chart_window = int(get_ui_setting_helper('chart_window_runs', '200'))
        runs = get_recent_scan_runs(db_path, limit=chart_window)

        # Get new/unsafe hosts for quick actions
        all_hosts = get_hosts_with_profiles(db_path)
        new_hosts = [h for h in all_hosts if h.get('profile_is_safe') != 1 and h['last_status'] == 'up']

        # Get IPv6 neighbor count (last hour)
        ipv6_enabled = get_ui_setting_helper('ipv6_passive_enabled', 'true').lower() == 'true'
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

        return render_template('dashboard.tpl', stats=stats, chart_data_json=chart_data_json,
                                auth_enabled=auth.config.auth_enabled, new_hosts=new_hosts[:10],
                                ipv6_enabled=ipv6_enabled, ipv6_count=ipv6_count)

    @app.route('/partials/summary')
    @auth.require_auth
    def partials_summary():
        stats = get_scan_stats(db_path)

        # Get IPv6 neighbor count (last hour)
        ipv6_enabled = get_ui_setting_helper('ipv6_passive_enabled', 'true').lower() == 'true'
        ipv6_count = 0
        if ipv6_enabled:
            from pyngding.scanning.ipv6 import get_recent_ipv6_neighbors
            ipv6_neighbors = get_recent_ipv6_neighbors(db_path, hours=1)
            ipv6_count = len(ipv6_neighbors)

        return render_template('partials/summary.tpl', stats=stats, ipv6_enabled=ipv6_enabled, ipv6_count=ipv6_count)

    @app.route('/partials/recent-changes')
    @auth.require_auth
    def partials_recent_changes():
        recent_runs = get_recent_scan_runs(db_path, limit=10)
        return render_template('partials/recent-changes.tpl', runs=recent_runs)

