"""SQLite database initialization and core queries."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional


@contextmanager
def get_db(db_path: str):
    """Context manager for database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    """Initialize database schema with WAL mode and all tables."""
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    with get_db(db_path) as conn:
        # Set PRAGMAs
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        
        # Table 1: hosts (current view per IP)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE NOT NULL,
                mac TEXT NULL,
                hostname TEXT NULL,
                vendor TEXT NULL,
                first_seen_ts INTEGER NOT NULL,
                last_seen_ts INTEGER NOT NULL,
                last_status TEXT NOT NULL,
                last_rtt_ms INTEGER NULL
            )
        """)
        
        # Table 2: scan_runs
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_ts INTEGER NOT NULL,
                finished_ts INTEGER NOT NULL,
                targets_count INTEGER NOT NULL,
                up_count INTEGER NOT NULL,
                down_count INTEGER NOT NULL
            )
        """)
        
        # Table 3: observations (raw scan history)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                ip TEXT NOT NULL,
                status TEXT NOT NULL,
                rtt_ms INTEGER NULL,
                mac TEXT NULL,
                hostname TEXT NULL,
                FOREIGN KEY (run_id) REFERENCES scan_runs(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_observations_run_id ON observations(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_observations_ip ON observations(ip)")
        
        # Table 4: device_profiles (admin inventory metadata)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS device_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mac TEXT UNIQUE NULL,
                ip_key TEXT UNIQUE NULL,
                label TEXT NULL,
                is_safe INTEGER NOT NULL DEFAULT 0,
                tags TEXT NULL,
                notes TEXT NULL,
                created_ts INTEGER NOT NULL,
                updated_ts INTEGER NOT NULL
            )
        """)
        
        # Table 5: stats_daily (rollups)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats_daily (
                day_yyyymmdd INTEGER PRIMARY KEY,
                runs INTEGER NOT NULL,
                avg_up_count REAL NOT NULL,
                max_up_count INTEGER NOT NULL,
                new_hosts INTEGER NOT NULL,
                vanished_hosts INTEGER NOT NULL
            )
        """)
        
        # Table 6: ui_settings
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ui_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Table 7: api_keys
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                created_ts INTEGER NOT NULL,
                last_used_ts INTEGER NULL,
                is_enabled INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        # Table 8: dns_events (AdGuard DNS ingestion)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dns_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                client_ip TEXT NOT NULL,
                domain TEXT NOT NULL,
                qtype TEXT NULL,
                status TEXT NULL,
                upstream TEXT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dns_events_ts ON dns_events(ts)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dns_events_client_ip_ts ON dns_events(client_ip, ts)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dns_events_domain ON dns_events(domain)")
        
        # Table 9: dns_daily_client (cheap rollup)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dns_daily_client (
                day_yyyymmdd INTEGER NOT NULL,
                client_ip TEXT NOT NULL,
                total_queries INTEGER NOT NULL,
                blocked_queries INTEGER NOT NULL,
                unique_domains INTEGER NOT NULL,
                PRIMARY KEY (day_yyyymmdd, client_ip)
            )
        """)
        
        # Table 10: ipv6_neighbors (passive IPv6)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ipv6_neighbors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                ip6 TEXT NOT NULL,
                mac TEXT NULL,
                state TEXT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ipv6_neighbors_ts ON ipv6_neighbors(ts)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ipv6_neighbors_ip6 ON ipv6_neighbors(ip6)")


# Core query functions

def get_host(db_path: str, ip: str) -> Optional[Dict]:
    """Get a host by IP."""
    with get_db(db_path) as conn:
        row = conn.execute("SELECT * FROM hosts WHERE ip = ?", (ip,)).fetchone()
        return dict(row) if row else None


def upsert_host(db_path: str, ip: str, mac: Optional[str] = None, hostname: Optional[str] = None,
                vendor: Optional[str] = None, status: str = "up", rtt_ms: Optional[int] = None,
                now_ts: Optional[int] = None) -> None:
    """Insert or update a host record."""
    import time
    if now_ts is None:
        now_ts = int(time.time())
    
    with get_db(db_path) as conn:
        existing = conn.execute("SELECT id, first_seen_ts FROM hosts WHERE ip = ?", (ip,)).fetchone()
        if existing:
            # Update existing
            conn.execute("""
                UPDATE hosts SET
                    mac = COALESCE(?, mac),
                    hostname = COALESCE(?, hostname),
                    vendor = COALESCE(?, vendor),
                    last_seen_ts = ?,
                    last_status = ?,
                    last_rtt_ms = ?
                WHERE ip = ?
            """, (mac, hostname, vendor, now_ts, status, rtt_ms, ip))
        else:
            # Insert new
            conn.execute("""
                INSERT INTO hosts (ip, mac, hostname, vendor, first_seen_ts, last_seen_ts, last_status, last_rtt_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ip, mac, hostname, vendor, now_ts, now_ts, status, rtt_ms))


def create_scan_run(db_path: str, started_ts: int, finished_ts: int, targets_count: int,
                   up_count: int, down_count: int) -> int:
    """Create a scan run and return its ID."""
    with get_db(db_path) as conn:
        cursor = conn.execute("""
            INSERT INTO scan_runs (started_ts, finished_ts, targets_count, up_count, down_count)
            VALUES (?, ?, ?, ?, ?)
        """, (started_ts, finished_ts, targets_count, up_count, down_count))
        return cursor.lastrowid


def insert_observation(db_path: str, run_id: int, ip: str, status: str,
                       rtt_ms: Optional[int] = None, mac: Optional[str] = None,
                       hostname: Optional[str] = None) -> None:
    """Insert an observation record."""
    with get_db(db_path) as conn:
        conn.execute("""
            INSERT INTO observations (run_id, ip, status, rtt_ms, mac, hostname)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (run_id, ip, status, rtt_ms, mac, hostname))


def get_all_hosts(db_path: str, status: Optional[str] = None) -> List[Dict]:
    """Get all hosts, optionally filtered by status."""
    with get_db(db_path) as conn:
        if status:
            rows = conn.execute("SELECT * FROM hosts WHERE last_status = ? ORDER BY ip", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM hosts ORDER BY ip").fetchall()
        return [dict(row) for row in rows]


def get_recent_scan_runs(db_path: str, limit: int = 200) -> List[Dict]:
    """Get recent scan runs for charting."""
    with get_db(db_path) as conn:
        rows = conn.execute("""
            SELECT * FROM scan_runs
            ORDER BY started_ts DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]


def get_ui_setting(db_path: str, key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a UI setting value."""
    with get_db(db_path) as conn:
        row = conn.execute("SELECT value FROM ui_settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default


def set_ui_setting(db_path: str, key: str, value: str) -> None:
    """Set a UI setting value."""
    with get_db(db_path) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO ui_settings (key, value)
            VALUES (?, ?)
        """, (key, value))


def get_device_profile(db_path: str, mac: Optional[str] = None, ip: Optional[str] = None) -> Optional[Dict]:
    """Get device profile by MAC or IP."""
    with get_db(db_path) as conn:
        if mac:
            row = conn.execute("SELECT * FROM device_profiles WHERE mac = ?", (mac,)).fetchone()
        elif ip:
            row = conn.execute("SELECT * FROM device_profiles WHERE ip_key = ?", (f"ip:{ip}",)).fetchone()
        else:
            return None
        return dict(row) if row else None


def upsert_device_profile(db_path: str, mac: Optional[str] = None, ip: Optional[str] = None,
                         label: Optional[str] = None, is_safe: bool = False,
                         tags: Optional[str] = None, notes: Optional[str] = None,
                         now_ts: Optional[int] = None) -> int:
    """Create or update a device profile. Returns profile ID."""
    import time
    if now_ts is None:
        now_ts = int(time.time())
    
    with get_db(db_path) as conn:
        # Check if exists
        existing = None
        if mac:
            existing = conn.execute("SELECT id FROM device_profiles WHERE mac = ?", (mac,)).fetchone()
        elif ip:
            ip_key = f"ip:{ip}"
            existing = conn.execute("SELECT id FROM device_profiles WHERE ip_key = ?", (ip_key,)).fetchone()
        
        if existing:
            # Update
            profile_id = existing[0]
            conn.execute("""
                UPDATE device_profiles SET
                    label = COALESCE(?, label),
                    is_safe = ?,
                    tags = COALESCE(?, tags),
                    notes = COALESCE(?, notes),
                    updated_ts = ?
                WHERE id = ?
            """, (label, 1 if is_safe else 0, tags, notes, now_ts, profile_id))
            return profile_id
        else:
            # Insert
            ip_key = f"ip:{ip}" if ip and not mac else None
            cursor = conn.execute("""
                INSERT INTO device_profiles (mac, ip_key, label, is_safe, tags, notes, created_ts, updated_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (mac, ip_key, label, 1 if is_safe else 0, tags, notes, now_ts, now_ts))
            return cursor.lastrowid


def get_all_device_profiles(db_path: str) -> List[Dict]:
    """Get all device profiles."""
    with get_db(db_path) as conn:
        rows = conn.execute("SELECT * FROM device_profiles ORDER BY updated_ts DESC").fetchall()
        return [dict(row) for row in rows]


def delete_device_profile(db_path: str, profile_id: int) -> bool:
    """Delete a device profile by ID."""
    with get_db(db_path) as conn:
        cursor = conn.execute("DELETE FROM device_profiles WHERE id = ?", (profile_id,))
        return cursor.rowcount > 0


def get_hosts_with_profiles(db_path: str) -> List[Dict]:
    """Get all hosts with their device profile information joined."""
    with get_db(db_path) as conn:
        rows = conn.execute("""
            SELECT h.*, 
                   dp.id as profile_id,
                   dp.label as profile_label,
                   dp.is_safe as profile_is_safe,
                   dp.tags as profile_tags,
                   dp.notes as profile_notes
            FROM hosts h
            LEFT JOIN device_profiles dp ON (
                (h.mac IS NOT NULL AND dp.mac = h.mac) OR
                (h.mac IS NULL AND dp.ip_key = 'ip:' || h.ip)
            )
            ORDER BY h.ip
        """).fetchall()
        return [dict(row) for row in rows]

