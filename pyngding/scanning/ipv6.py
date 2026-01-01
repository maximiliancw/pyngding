"""IPv6 passive neighbor collection."""
import subprocess
import time


def get_ipv6_neighbors() -> list[dict]:
    """Get IPv6 neighbors from 'ip -6 neigh show'.

    Returns list of dicts with keys: ip6, mac, state
    """
    neighbors = []
    try:
        result = subprocess.run(
            ['ip', '-6', 'neigh', 'show'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse lines like: "fe80::1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE"
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 3:
                    ip6 = parts[0]
                    mac = None
                    state = None

                    # Find lladdr (MAC address)
                    for i, part in enumerate(parts):
                        if part == 'lladdr' and i + 1 < len(parts):
                            mac = parts[i + 1]
                            break

                    # Find state (last word, typically REACHABLE, STALE, etc.)
                    if len(parts) > 1:
                        state = parts[-1]

                    if ip6:
                        neighbors.append({
                            'ip6': ip6,
                            'mac': mac,
                            'state': state
                        })
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        # Best effort - if ip command fails, continue without IPv6 data
        print(f"Warning: Could not get IPv6 neighbors: {e}", file=__import__('sys').stderr)

    return neighbors


def collect_ipv6_neighbors(db_path: str) -> int:
    """Collect IPv6 neighbors and store in database.

    Returns number of neighbors collected.
    """
    from pyngding.core.db import get_db

    neighbors = get_ipv6_neighbors()
    if not neighbors:
        return 0

    now_ts = int(time.time())
    count = 0

    with get_db(db_path) as conn:
        for neighbor in neighbors:
            conn.execute("""
                INSERT INTO ipv6_neighbors (ts, ip6, mac, state)
                VALUES (?, ?, ?, ?)
            """, (now_ts, neighbor['ip6'], neighbor.get('mac'), neighbor.get('state')))
            count += 1

    return count


def get_recent_ipv6_neighbors(db_path: str, hours: int = 1) -> list[dict]:
    """Get IPv6 neighbors seen in the last N hours."""
    from pyngding.core.db import get_db

    cutoff_ts = int(time.time()) - (hours * 3600)

    with get_db(db_path) as conn:
        rows = conn.execute("""
            SELECT DISTINCT ip6, mac, state, MAX(ts) as last_seen
            FROM ipv6_neighbors
            WHERE ts >= ?
            GROUP BY ip6, mac, state
            ORDER BY last_seen DESC
        """, (cutoff_ts,)).fetchall()

        return [dict(row) for row in rows]

