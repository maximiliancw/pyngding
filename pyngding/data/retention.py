"""Data retention and rollup management."""
import time
from typing import Dict, Optional


def run_retention(db_path: str) -> Dict[str, int]:
    """Run retention cleanup and rollups.
    
    Returns dict with counts of deleted records.
    """
    from pyngding.core.db import get_ui_setting, get_db
    from pyngding.web.settings import DEFAULTS
    
    now_ts = int(time.time())
    deleted = {
        'observations': 0,
        'dns_events': 0,
        'scan_runs': 0,
    }
    
    with get_db(db_path) as conn:
        # Prune observations
        obs_retention_days = int(get_ui_setting(db_path, 'raw_observation_retention_days', DEFAULTS['raw_observation_retention_days']))
        if obs_retention_days > 0:
            cutoff_ts = now_ts - (obs_retention_days * 86400)
            cursor = conn.execute("""
                DELETE FROM observations
                WHERE run_id IN (
                    SELECT id FROM scan_runs WHERE started_ts < ?
                )
            """, (cutoff_ts,))
            deleted['observations'] = cursor.rowcount
        
        # Prune DNS events
        dns_retention_days = int(get_ui_setting(db_path, 'dns_event_retention_days', DEFAULTS['dns_event_retention_days']))
        if dns_retention_days > 0:
            cutoff_ts = now_ts - (dns_retention_days * 86400)
            cursor = conn.execute("DELETE FROM dns_events WHERE ts < ?", (cutoff_ts,))
            deleted['dns_events'] = cursor.rowcount
        
        # Prune scan runs (but keep stats_daily)
        scan_retention_days = int(get_ui_setting(db_path, 'scan_run_retention_days', DEFAULTS['scan_run_retention_days']))
        if scan_retention_days > 0:
            cutoff_ts = now_ts - (scan_retention_days * 86400)
            cursor = conn.execute("DELETE FROM scan_runs WHERE started_ts < ?", (cutoff_ts,))
            deleted['scan_runs'] = cursor.rowcount
        
        # Prune old IPv6 neighbors (keep last 7 days)
        ipv6_cutoff_ts = now_ts - (7 * 86400)
        cursor = conn.execute("DELETE FROM ipv6_neighbors WHERE ts < ?", (ipv6_cutoff_ts,))
        deleted['ipv6_neighbors'] = cursor.rowcount
    
    return deleted


def update_daily_stats(db_path: str, day_yyyymmdd: Optional[int] = None) -> None:
    """Update or create daily statistics rollup.
    
    If day_yyyymmdd is None, uses today.
    """
    import time
    from pyngding.core.db import get_db
    
    if day_yyyymmdd is None:
        day_yyyymmdd = int(time.strftime('%Y%m%d', time.localtime()))
    
    day_start_ts = int(time.mktime(time.strptime(str(day_yyyymmdd), '%Y%m%d')))
    day_end_ts = day_start_ts + 86400
    
    with get_db(db_path) as conn:
        # Get scan runs for this day
        runs = conn.execute("""
            SELECT COUNT(*) as runs,
                   AVG(up_count) as avg_up,
                   MAX(up_count) as max_up
            FROM scan_runs
            WHERE started_ts >= ? AND started_ts < ?
        """, (day_start_ts, day_end_ts)).fetchone()
        
        runs_count = runs[0] if runs and runs[0] else 0
        avg_up = runs[1] if runs and runs[1] else 0.0
        max_up = runs[2] if runs and runs[2] else 0
        
        # Count new hosts (first_seen on this day)
        new_hosts = conn.execute("""
            SELECT COUNT(*) FROM hosts
            WHERE first_seen_ts >= ? AND first_seen_ts < ?
        """, (day_start_ts, day_end_ts)).fetchone()[0] or 0
        
        # Count vanished hosts (last_seen before this day, but first_seen before this day)
        # This is approximate - a host is "vanished" if it was seen before but not on this day
        vanished_hosts = conn.execute("""
            SELECT COUNT(*) FROM hosts
            WHERE first_seen_ts < ? AND last_seen_ts < ?
        """, (day_start_ts, day_start_ts)).fetchone()[0] or 0
        
        # Insert or update stats
        conn.execute("""
            INSERT OR REPLACE INTO stats_daily (day_yyyymmdd, runs, avg_up_count, max_up_count, new_hosts, vanished_hosts)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (day_yyyymmdd, runs_count, avg_up, max_up, new_hosts, vanished_hosts))


def run_rollups(db_path: str) -> None:
    """Run all rollups (daily stats for recent days)."""
    import time
    
    # Update stats for last 7 days
    for i in range(7):
        day_ts = int(time.time()) - (i * 86400)
        day_yyyymmdd = int(time.strftime('%Y%m%d', time.localtime(day_ts)))
        update_daily_stats(db_path, day_yyyymmdd)

