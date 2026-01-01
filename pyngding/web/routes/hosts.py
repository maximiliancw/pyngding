"""Hosts page routes."""
from bottle import request

from pyngding.core.db import get_all_hosts, get_host_dns_summary
from pyngding.core.db import get_ui_setting as db_get_ui_setting
from pyngding.web.middleware import AuthMiddleware
from pyngding.web.settings import DEFAULTS


def register_routes(app, auth: AuthMiddleware, db_path: str, render_template):
    """Register hosts routes on the app."""
    
    def get_ui_setting_helper(key: str, default: str) -> str:
        return db_get_ui_setting(db_path, key, default)

    def filter_hosts(hosts: list[dict], search: str) -> list[dict]:
        """Filter hosts by search term."""
        if not search:
            return hosts
        filtered = []
        for host in hosts:
            if (search in host['ip'].lower() or
                (host['hostname'] and search in host['hostname'].lower()) or
                (host['mac'] and search in host['mac'].lower()) or
                (host['vendor'] and search in host['vendor'].lower())):
                filtered.append(host)
        return filtered

    @app.route('/hosts')
    @auth.require_auth
    def hosts():
        status_filter = request.query.get('status', '').strip()
        search = request.query.get('search', '').strip().lower()

        all_hosts = get_all_hosts(db_path, status=status_filter if status_filter else None)
        all_hosts = filter_hosts(all_hosts, search)

        return render_template('hosts.tpl', hosts=all_hosts, status_filter=status_filter, 
                              search=search, auth_enabled=auth.config.auth_enabled)

    @app.route('/partials/hosts-table')
    @auth.require_auth
    def partials_hosts_table():
        status_filter = request.query.get('status', '').strip()
        search = request.query.get('search', '').strip().lower()

        all_hosts = get_all_hosts(db_path, status=status_filter if status_filter else None)
        all_hosts = filter_hosts(all_hosts, search)

        return render_template('partials/hosts-table.tpl', hosts=all_hosts)

    @app.route('/partials/dns-host/<ip>')
    @auth.require_auth
    def partials_dns_host(ip):
        adguard_enabled = get_ui_setting_helper('adguard_enabled', DEFAULTS['adguard_enabled']).lower() == 'true'
        if not adguard_enabled:
            return render_template('partials/dns-host.tpl', enabled=False, ip=ip)

        summary = get_host_dns_summary(db_path, ip, limit=20)
        return render_template('partials/dns-host.tpl', enabled=True, ip=ip, summary=summary)

