"""IPv4 scanner: ping reachability + MAC enrichment + reverse DNS."""
import ipaddress
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError


def parse_targets(targets_str: str, target_cap: int = 4096) -> list[str]:
    """Parse scan targets from config string.

    Supports:
    - CIDR notation: 192.168.1.0/24
    - Ranges: 192.168.1.1-192.168.1.50
    - Comma-separated list

    Returns list of IP addresses as strings.
    """
    ip_set: set[str] = set()
    parts = [p.strip() for p in targets_str.split(',') if p.strip()]

    for part in parts:
        # Try CIDR notation
        if '/' in part:
            try:
                network = ipaddress.ip_network(part, strict=False)
                for ip in network.hosts():  # Excludes network/broadcast
                    ip_set.add(str(ip))
            except ValueError:
                continue

        # Try range notation: a.b.c.d-a.b.c.z
        elif '-' in part:
            try:
                start_str, end_str = part.split('-', 1)
                start_ip = ipaddress.ip_address(start_str.strip())
                end_ip = ipaddress.ip_address(end_str.strip())

                # Only support ranges within same /24 for safety
                if start_ip.version == 4 and end_ip.version == 4:
                    start_int = int(start_ip)
                    end_int = int(end_ip)
                    if 0 <= (end_int - start_int) <= 255:  # Limit to 256 IPs
                        for ip_int in range(start_int, end_int + 1):
                            ip_set.add(str(ipaddress.ip_address(ip_int)))
            except (ValueError, AttributeError):
                continue

        # Try single IP
        else:
            try:
                ip = ipaddress.ip_address(part)
                if ip.version == 4:
                    ip_set.add(str(ip))
            except ValueError:
                continue

    # Apply cap
    ip_list = sorted(list(ip_set))[:target_cap]
    return ip_list


def get_mac_mapping() -> dict[str, str]:
    """Get IP -> MAC mapping from 'ip neigh show'."""
    mapping = {}
    try:
        result = subprocess.run(
            ['ip', 'neigh', 'show'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse lines like: "192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE"
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5:
                    ip = parts[0]
                    # Find lladdr (MAC address)
                    for i, part in enumerate(parts):
                        if part == 'lladdr' and i + 1 < len(parts):
                            mac = parts[i + 1]
                            mapping[ip] = mac
                            break
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Best effort - if ip command fails, continue without MACs
        pass

    return mapping


def ping_host(ip: str, timeout: float = 1.0, count: int = 1) -> tuple[bool, int | None]:
    """Ping a host and return (is_up, rtt_ms).

    Uses Linux ping command: ping -c {count} -W {timeout} {ip}
    """
    try:
        # Linux ping: -W is timeout in seconds, -c is count
        result = subprocess.run(
            ['ping', '-c', str(count), '-W', str(int(timeout)), ip],
            capture_output=True,
            text=True,
            timeout=timeout + 1.0
        )

        is_up = result.returncode == 0

        # Try to parse RTT from output (best effort)
        rtt_ms = None
        if is_up:
            # Look for pattern like "time=1.23 ms" or "time=1.23ms"
            match = re.search(r'time[=<](\d+\.?\d*)\s*ms', result.stdout)
            if match:
                try:
                    rtt_ms = int(float(match.group(1)))
                except (ValueError, AttributeError):
                    pass

        return is_up, rtt_ms

    except subprocess.TimeoutExpired:
        return False, None
    except Exception:
        return False, None


def reverse_dns_lookup(ip: str, timeout: float = 0.5) -> str | None:
    """Perform reverse DNS lookup for an IP address.

    Returns hostname or None if lookup fails or times out.
    """
    try:
        # Use socket with timeout
        socket.setdefaulttimeout(timeout)
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (TimeoutError, socket.herror, socket.gaierror, OSError):
        return None
    finally:
        socket.setdefaulttimeout(None)


def scan_targets(targets: list[str], ping_timeout: float = 1.0, ping_count: int = 1,
                 max_workers: int = 32, reverse_dns: bool = False) -> list[dict]:
    """Scan a list of IP targets and return results.

    Returns list of dicts with keys: ip, status, rtt_ms, mac, hostname
    """
    # Get MAC mapping once
    mac_mapping = get_mac_mapping()

    results = []

    def scan_one(ip: str) -> dict:
        """Scan a single IP."""
        is_up, rtt_ms = ping_host(ip, timeout=ping_timeout, count=ping_count)
        status = "up" if is_up else "down"

        mac = mac_mapping.get(ip)
        hostname = None

        # Only do reverse DNS for hosts that are up (to avoid slowing down scans)
        if is_up and reverse_dns:
            hostname = reverse_dns_lookup(ip, timeout=0.5)

        return {
            'ip': ip,
            'status': status,
            'rtt_ms': rtt_ms,
            'mac': mac,
            'hostname': hostname
        }

    # Scan with bounded concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_one, ip): ip for ip in targets}

        for future in futures:
            try:
                result = future.result(timeout=ping_timeout + 2.0)
                results.append(result)
            except FutureTimeoutError:
                ip = futures[future]
                results.append({
                    'ip': ip,
                    'status': 'down',
                    'rtt_ms': None,
                    'mac': None,
                    'hostname': None
                })
            except Exception:
                ip = futures[future]
                results.append({
                    'ip': ip,
                    'status': 'down',
                    'rtt_ms': None,
                    'mac': None,
                    'hostname': None
                })

    return results

