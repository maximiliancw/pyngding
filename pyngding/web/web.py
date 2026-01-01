"""Bottle web application."""
import json
import time
from pathlib import Path

from bottle import Bottle, abort, request, response, static_file, template

from pyngding.core.config import Config
from pyngding.core.db import get_db
from pyngding.core.db import get_ui_setting as db_get_ui_setting
from pyngding.scanning.scheduler import ScanScheduler, get_scan_stats
from pyngding.web.middleware import AuthMiddleware
from pyngding.web.routes import admin, api, dashboard, hosts


def create_app(config: Config, db_path: str, scheduler: ScanScheduler) -> Bottle:
    """Create and configure the Bottle application."""
    app = Bottle()

    # Get absolute path to templates and static directories
    # This works whether running from source or installed package
    package_dir = Path(__file__).resolve().parent.parent
    templates_dir = package_dir / 'templates'
    static_dir = package_dir / 'static'

    # Ensure paths exist
    if not templates_dir.exists():
        raise RuntimeError(f"Templates directory not found: {templates_dir}")
    if not static_dir.exists():
        raise RuntimeError(f"Static directory not found: {static_dir}")

    # Convert to absolute path strings for Bottle
    templates_path = str(templates_dir.resolve())
    static_path = str(static_dir.resolve())

    # Configure Bottle's default template lookup
    # This sets the default lookup path for all template() calls
    import bottle
    # Clear any existing paths and set ours
    bottle.TEMPLATE_PATH.clear()
    bottle.TEMPLATE_PATH.insert(0, templates_path)

    # Create a helper function that always uses our template path
    def render_template(template_name, **kwargs):
        """Render a template with the correct lookup path."""
        # Make time module available to all templates
        kwargs['time'] = time
        return template(template_name, template_lookup=[templates_path], **kwargs)

    # Store it in app for use in routes
    app.render_template = render_template

    # Create auth middleware
    auth = AuthMiddleware(config, db_path)

    # Static files (no auth required)
    @app.route('/static/<filename:path>')
    def serve_static(filename):
        return static_file(filename, root=static_path)

    # Health endpoint (no auth required - standard health check)
    @app.route('/health')
    def health():
        """Health check endpoint with system stats."""

        health_data = {
            'status': 'ok',
            'timestamp': int(time.time()),
            'version': '1.0.0',
        }

        # Check database connectivity
        db_healthy = False
        try:
            with get_db(db_path) as conn:
                conn.execute("SELECT 1").fetchone()
                db_healthy = True
        except Exception as e:
            health_data['database_error'] = str(e)

        # Get scan stats
        try:
            stats = get_scan_stats(db_path)
            health_data['stats'] = {
                'hosts_up': stats.get('up_count', 0),
                'hosts_down': stats.get('down_count', 0),
                'total_hosts': stats.get('total_hosts', 0),
                'missing_count': stats.get('missing_count', 0),
                'last_scan_ts': stats.get('last_scan_ts'),
            }

            # Get additional stats
            with get_db(db_path) as conn:
                total_runs = conn.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0] or 0
                total_observations = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0] or 0
                total_dns_events = conn.execute("SELECT COUNT(*) FROM dns_events").fetchone()[0] or 0

                health_data['stats']['total_scan_runs'] = total_runs
                health_data['stats']['total_observations'] = total_observations
                health_data['stats']['total_dns_events'] = total_dns_events
        except Exception as e:
            health_data['stats_error'] = str(e)

        # Check scheduler status if available
        try:
            if scheduler:
                health_data['scheduler'] = {
                    'running': getattr(scheduler, 'running', None),
                    'adguard_running': getattr(scheduler, 'adguard_running', None),
                    'ipv6_running': getattr(scheduler, 'ipv6_running', None),
                }
        except Exception:
            pass  # Scheduler info is optional

        # Determine overall health status
        if not db_healthy:
            health_data['status'] = 'degraded'
            response.status = 503
        else:
            response.status = 200

        response.content_type = 'application/json'
        return json.dumps(health_data, indent=2)

    # Metrics endpoint (only when auth enabled AND metrics_enabled)
    @app.route('/metrics')
    def metrics():
        if not config.auth_enabled:
            abort(404, 'Not found')
        auth.check_auth()

        metrics_enabled = db_get_ui_setting(db_path, 'metrics_enabled', 'true').lower() == 'true'
        if not metrics_enabled:
            abort(404, 'Metrics disabled')

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

    # Register route modules
    dashboard.register_routes(app, auth, db_path, render_template)
    hosts.register_routes(app, auth, db_path, render_template)
    admin.register_routes(app, auth, db_path, render_template)
    api.register_routes(app, auth, db_path)

    return app


if __name__ == '__main__':
    """Development server - run directly for testing."""
    from pyngding.core.config import load_config
    from pyngding.core.db import init_db

    # Try to load config, or use defaults
    config_path = Path('config.ini')
    if config_path.exists():
        config = load_config(str(config_path))
    else:
        # Use default config for development
        config = Config()
        config.bind_host = '0.0.0.0'
        config.bind_port = 8080
        config.db_path = 'pyngding.sqlite'
        config.scan_targets = '192.168.1.0/24'
        config.scan_interval_seconds = 60
        config.auth_enabled = False

    # Initialize database
    init_db(config.db_path)

    # Create scheduler
    scheduler = ScanScheduler(config, config.db_path)
    scheduler.start()

    # Create app
    app = create_app(config, config.db_path, scheduler)
    print(f"Starting development server on http://{config.bind_host}:{config.bind_port}")
    app.run(host=config.bind_host, port=config.bind_port, debug=True)
