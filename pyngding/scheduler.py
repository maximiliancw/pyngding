"""Background scan scheduler."""
import signal
import threading
import time
from typing import Optional

from pyngding.config import Config
from pyngding.db import (
    create_scan_run,
    get_all_hosts,
    get_ui_setting,
    insert_observation,
    upsert_host,
)
from pyngding.scanner import parse_targets, scan_targets
from pyngding.adguard import fetch_adguard_api, read_adguard_file
from pyngding.db import (
    insert_dns_event,
    get_adguard_state,
    set_adguard_state,
    update_dns_daily_rollup,
)


class ScanScheduler:
    """Manages periodic scanning in a background thread."""
    
    def __init__(self, config: Config, db_path: str):
        self.config = config
        self.db_path = db_path
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # AdGuard scheduler
        self.adguard_running = False
        self.adguard_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the scan scheduler thread and AdGuard ingestion if enabled."""
        if self.running:
            return
        
        self.running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        # Start AdGuard ingestion if enabled
        adguard_enabled = get_ui_setting(self.db_path, 'adguard_enabled', 'false').lower() == 'true'
        if adguard_enabled:
            self.start_adguard()
    
    def start_adguard(self):
        """Start AdGuard ingestion thread."""
        if self.adguard_running:
            return
        
        self.adguard_running = True
        self.adguard_thread = threading.Thread(target=self._adguard_loop, daemon=True)
        self.adguard_thread.start()
    
    def stop(self):
        """Stop the scan scheduler thread and AdGuard ingestion."""
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5.0)
        
        self.adguard_running = False
        if self.adguard_thread:
            self.adguard_thread.join(timeout=5.0)
    
    def _run_loop(self):
        """Main scan loop."""
        while self.running and not self.stop_event.is_set():
            try:
                self._run_scan()
            except Exception as e:
                print(f"Error in scan loop: {e}", file=__import__('sys').stderr)
            
            # Wait for next interval (or stop if event is set)
            if not self.stop_event.wait(self.config.scan_interval_seconds):
                continue
            else:
                break
    
    def _run_scan(self):
        """Run a single scan."""
        started_ts = int(time.time())
        
        # Parse targets
        targets = parse_targets(self.config.scan_targets, self.config.target_cap)
        if not targets:
            return
        
        # Get reverse_dns setting (default True)
        reverse_dns = get_ui_setting(self.db_path, 'reverse_dns', 'true').lower() == 'true'
        
        # Run scan
        results = scan_targets(
            targets=targets,
            ping_timeout=self.config.ping_timeout_seconds,
            ping_count=self.config.ping_count,
            max_workers=self.config.max_workers,
            reverse_dns=reverse_dns
        )
        
        finished_ts = int(time.time())
        
        # Count up/down
        up_count = sum(1 for r in results if r['status'] == 'up')
        down_count = len(results) - up_count
        
        # Create scan run
        run_id = create_scan_run(
            self.db_path,
            started_ts=started_ts,
            finished_ts=finished_ts,
            targets_count=len(targets),
            up_count=up_count,
            down_count=down_count
        )
        
        # Get existing hosts for comparison
        existing_hosts = {h['ip']: h for h in get_all_hosts(self.db_path)}
        
        # Write observations and update hosts
        for result in results:
            ip = result['ip']
            existing = existing_hosts.get(ip)
            
            # Insert observation
            insert_observation(
                self.db_path,
                run_id=run_id,
                ip=ip,
                status=result['status'],
                rtt_ms=result.get('rtt_ms'),
                mac=result.get('mac'),
                hostname=result.get('hostname')
            )
            
            # Check for changes
            is_new = existing is None
            is_gone = existing and existing['last_status'] == 'up' and result['status'] == 'down'
            ip_mac_change = False
            if existing and result.get('mac') and existing.get('mac'):
                if result['mac'] != existing['mac']:
                    ip_mac_change = True
            
            # Get vendor from OUI lookup
            vendor = None
            if result.get('mac'):
                from pyngding.vendor import get_vendor
                vendor = get_vendor(result['mac'], self.db_path)
            
            # Update host record
            upsert_host(
                self.db_path,
                ip=ip,
                mac=result.get('mac'),
                hostname=result.get('hostname'),
                vendor=vendor,
                status=result['status'],
                rtt_ms=result.get('rtt_ms'),
                now_ts=finished_ts
            )
            
            # Send notifications
            from pyngding.db import get_device_profile
            from pyngding.notifications import send_notification
            
            profile = get_device_profile(self.db_path, mac=result.get('mac'), ip=ip)
            label = profile['label'] if profile else None
            is_safe = bool(profile['is_safe']) if profile else False
            tags = profile['tags'] if profile else None
            
            if is_new and result['status'] == 'up':
                send_notification(
                    self.db_path, 'new_host', ip,
                    mac=result.get('mac'), hostname=result.get('hostname'),
                    vendor=None, label=label, is_safe=is_safe, tags=tags
                )
            elif is_gone:
                send_notification(
                    self.db_path, 'host_gone', ip,
                    mac=result.get('mac'), hostname=result.get('hostname'),
                    vendor=None, label=label, is_safe=is_safe, tags=tags
                )
            elif ip_mac_change:
                send_notification(
                    self.db_path, 'ip_mac_change', ip,
                    mac=result.get('mac'), hostname=result.get('hostname'),
                    vendor=None, label=label, is_safe=is_safe, tags=tags,
                    extra={'old_mac': existing.get('mac'), 'new_mac': result.get('mac')}
                )
        
        print(f"Scan completed: {up_count} up, {down_count} down, {len(targets)} targets")
    
    def _adguard_loop(self):
        """AdGuard ingestion loop."""
        while self.adguard_running and not self.stop_event.is_set():
            try:
                self._ingest_adguard()
            except Exception as e:
                print(f"Error in AdGuard ingestion: {e}", file=__import__('sys').stderr)
            
            # Get interval
            interval = int(get_ui_setting(self.db_path, 'adguard_ingest_interval_seconds', '30'))
            if not self.stop_event.wait(interval):
                continue
            else:
                break
    
    def _ingest_adguard(self):
        """Ingest DNS events from AdGuard."""
        from pyngding.settings import DEFAULTS
        
        adguard_enabled = get_ui_setting(self.db_path, 'adguard_enabled', 'false').lower() == 'true'
        if not adguard_enabled:
            return
        
        mode = get_ui_setting(self.db_path, 'adguard_mode', 'api')
        max_fetch = int(get_ui_setting(self.db_path, 'adguard_max_fetch', '500'))
        
        events = []
        
        if mode == 'api':
            base_url = get_ui_setting(self.db_path, 'adguard_base_url', '')
            username = get_ui_setting(self.db_path, 'adguard_username', '') or None
            password = get_ui_setting(self.db_path, 'adguard_password', '') or None
            
            if not base_url:
                return
            
            state = get_adguard_state(self.db_path)
            events = fetch_adguard_api(base_url, username, password, max_fetch, state['last_seen_ts'])
            
            if events:
                # Update last_seen_ts to most recent event
                latest_ts = max(e['ts'] for e in events)
                set_adguard_state(self.db_path, last_seen_ts=latest_ts)
        
        elif mode == 'file':
            file_path = get_ui_setting(self.db_path, 'adguard_querylog_path', '')
            if not file_path:
                return
            
            state = get_adguard_state(self.db_path)
            events, new_offset = read_adguard_file(file_path, state['last_offset'])
            set_adguard_state(self.db_path, last_offset=new_offset)
        
        # Insert events and update rollups
        now = int(time.time())
        today_yyyymmdd = int(time.strftime('%Y%m%d', time.localtime(now)))
        
        for event in events:
            insert_dns_event(
                self.db_path,
                ts=event['ts'],
                client_ip=event['client_ip'],
                domain=event['domain'],
                qtype=event.get('qtype'),
                status=event.get('status'),
                upstream=event.get('upstream')
            )
            
            # Update daily rollup (simplified - just increment)
            # In production, you'd want to batch these updates
            event_day = int(time.strftime('%Y%m%d', time.localtime(event['ts'])))
            blocked = 1 if event.get('status') == 'blocked' else 0
            update_dns_daily_rollup(
                self.db_path,
                day_yyyymmdd=event_day,
                client_ip=event['client_ip'],
                total_queries=1,
                blocked_queries=blocked,
                unique_domains=0  # Will be recalculated by SQL
            )
        
        if events:
            print(f"AdGuard: Ingested {len(events)} DNS events")


def get_scan_stats(db_path: str) -> dict:
    """Get basic dashboard statistics."""
    from pyngding.db import get_db
    
    stats = {
        'up_count': 0,
        'down_count': 0,
        'total_hosts': 0,
        'last_scan_ts': None,
        'new_since_last': 0,
        'missing_count': 0,
    }
    
    with get_db(db_path) as conn:
        # Get current host counts
        up_row = conn.execute("SELECT COUNT(*) FROM hosts WHERE last_status = 'up'").fetchone()
        down_row = conn.execute("SELECT COUNT(*) FROM hosts WHERE last_status = 'down'").fetchone()
        total_row = conn.execute("SELECT COUNT(*) FROM hosts").fetchone()
        
        stats['up_count'] = up_row[0] if up_row else 0
        stats['down_count'] = down_row[0] if down_row else 0
        stats['total_hosts'] = total_row[0] if total_row else 0
        
        # Get last scan time
        last_run = conn.execute("""
            SELECT finished_ts FROM scan_runs
            ORDER BY finished_ts DESC
            LIMIT 1
        """).fetchone()
        
        if last_run:
            stats['last_scan_ts'] = last_run[0]
        
        # Get missing threshold (default 10 minutes)
        missing_threshold_minutes = int(
            get_ui_setting(db_path, 'missing_threshold_minutes', '10')
        )
        missing_threshold_ts = int(time.time()) - (missing_threshold_minutes * 60)
        
        # Count missing hosts (previously seen but not seen recently)
        missing_row = conn.execute("""
            SELECT COUNT(*) FROM hosts
            WHERE last_status = 'up' AND last_seen_ts < ?
        """, (missing_threshold_ts,)).fetchone()
        
        stats['missing_count'] = missing_row[0] if missing_row else 0
    
    return stats

