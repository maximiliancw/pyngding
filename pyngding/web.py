"""Bottle web application."""
import base64
import json
import time
from bottle import Bottle, request, response, template, static_file, abort

from pyngding.auth import check_basic_auth
from pyngding.config import Config
from pyngding.db import get_all_hosts, get_recent_scan_runs, get_scan_stats, get_db, get_ui_setting as db_get_ui_setting
from pyngding.scheduler import ScanScheduler


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
        
        # Prepare chart data (reverse for chronological order)
        chart_data = {
            'labels': [f"Run {r['id']}" for r in reversed(runs)],
            'up_counts': [r['up_count'] for r in reversed(runs)]
        }
        chart_data_json = json.dumps(chart_data)
        
        return template('dashboard.tpl', stats=stats, chart_data_json=chart_data_json, auth_enabled=config.auth_enabled)
    
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
    
    # Admin routes (only accessible when auth is enabled)
    @app.route('/admin/<path:path>')
    def admin_404(path):
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()  # Require auth for admin routes
        abort(404, 'Admin route not yet implemented')
    
    # API routes (only accessible when auth is enabled AND api_enabled)
    @app.route('/api/<path:path>')
    def api_404(path):
        if not config.auth_enabled:
            abort(404, 'Not found')
        # API key check will be implemented in Step 11
        abort(404, 'API route not yet implemented')
    
    # Metrics endpoint (only when auth enabled AND metrics_enabled)
    @app.route('/metrics')
    def metrics():
        if not config.auth_enabled:
            abort(404, 'Not found')
        check_auth()  # Require auth for metrics
        
        metrics_enabled = get_ui_setting_helper(db_path, 'metrics_enabled', 'true').lower() == 'true'
        if not metrics_enabled:
            abort(404, 'Metrics disabled')
        
        # Metrics will be implemented in Step 17
        return "# Metrics endpoint (to be implemented in Step 17)\n"
    
    return app


def get_ui_setting_helper(db_path: str, key: str, default: str) -> str:
    """Helper to get UI setting."""
    return db_get_ui_setting(db_path, key, default)

