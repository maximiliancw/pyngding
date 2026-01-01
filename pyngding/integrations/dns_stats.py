"""DNS statistics and heuristics."""
import time


def detect_dns_burst(db_path: str, client_ip: str, window_minutes: int = 5,
                    threshold: int = 100) -> bool:
    """Detect if a host has a DNS burst (high query rate).

    Returns True if queries in last window_minutes exceed threshold.
    """
    from pyngding.core.db import get_db

    window_start = int(time.time()) - (window_minutes * 60)

    with get_db(db_path) as conn:
        count_row = conn.execute("""
            SELECT COUNT(*) FROM dns_events
            WHERE client_ip = ? AND ts >= ?
        """, (client_ip, window_start)).fetchone()

        count = count_row[0] if count_row else 0
        return count > threshold


def get_dns_burst_hosts(db_path: str, window_minutes: int = 5,
                        threshold: int = 100) -> list[dict]:
    """Get list of hosts with DNS bursts."""
    from pyngding.core.db import get_db, get_device_profile

    window_start = int(time.time()) - (window_minutes * 60)

    with get_db(db_path) as conn:
        # Get hosts with high query counts
        rows = conn.execute("""
            SELECT client_ip, COUNT(*) as cnt
            FROM dns_events
            WHERE ts >= ?
            GROUP BY client_ip
            HAVING cnt > ?
        """, (window_start, threshold)).fetchall()

        burst_hosts = []
        for row in rows:
            client_ip = row[0]
            count = row[1]

            # Check if device is marked safe
            profile = get_device_profile(db_path, ip=client_ip)
            is_safe = bool(profile['is_safe']) if profile else False

            if not is_safe:
                burst_hosts.append({
                    'ip': client_ip,
                    'query_count': count,
                    'window_minutes': window_minutes
                })

        return burst_hosts

