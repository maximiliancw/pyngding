"""Bottle web application."""
import json
import time
from bottle import Bottle, request, response, template, static_file

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
    
    # Static files
    @app.route('/static/<filename:path>')
    def serve_static(filename):
        return static_file(filename, root='pyngding/static')
    
    # Dashboard
    @app.route('/')
    def dashboard():
        stats = get_scan_stats(db_path)
        chart_window = int(get_ui_setting_helper(db_path, 'chart_window_runs', '200'))
        runs = get_recent_scan_runs(db_path, limit=chart_window)
        
        # Prepare chart data (reverse for chronological order)
        chart_data = {
            'labels': [f"Run {r['id']}" for r in reversed(runs)],
            'up_counts': [r['up_count'] for r in reversed(runs)]
        }
        chart_data_json = json.dumps(chart_data)
        
        return template('dashboard.tpl', stats=stats, chart_data_json=chart_data_json)
    
    # Hosts page
    @app.route('/hosts')
    def hosts():
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
        
        return template('hosts.tpl', hosts=all_hosts, status_filter=status_filter, search=search)
    
    # HTMX partials
    @app.route('/partials/summary')
    def partials_summary():
        stats = get_scan_stats(db_path)
        return template('partials/summary.tpl', stats=stats)
    
    @app.route('/partials/recent-changes')
    def partials_recent_changes():
        # Get recent scan runs
        recent_runs = get_recent_scan_runs(db_path, limit=10)
        return template('partials/recent-changes.tpl', runs=recent_runs)
    
    @app.route('/partials/hosts-table')
    def partials_hosts_table():
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
    
    return app


def get_ui_setting_helper(db_path: str, key: str, default: str) -> str:
    """Helper to get UI setting."""
    return db_get_ui_setting(db_path, key, default)

