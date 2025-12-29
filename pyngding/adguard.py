"""AdGuard Home integration for DNS query log ingestion."""
import json
import time
import urllib.request
import urllib.error
import base64
from typing import Dict, List, Optional, Tuple


def fetch_adguard_api(base_url: str, username: Optional[str] = None,
                     password: Optional[str] = None, max_fetch: int = 500,
                     last_seen_ts: Optional[int] = None) -> List[Dict]:
    """Fetch query log from AdGuard Home API.
    
    Returns list of DNS event dicts with keys: ts, client_ip, domain, qtype, status, upstream
    """
    try:
        # Build URL
        url = f"{base_url.rstrip('/')}/control/querylog"
        params = {'limit': max_fetch}
        if last_seen_ts:
            params['older_than'] = last_seen_ts
        
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        
        # Create request with auth if needed
        req = urllib.request.Request(full_url)
        if username and password:
            creds = base64.b64encode(f"{username}:{password}".encode()).decode()
            req.add_header('Authorization', f'Basic {creds}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            events = []
            for entry in data.get('data', []):
                # Parse AdGuard format
                # Typical fields: time, client, question, answer, status, upstream
                event = {
                    'ts': int(entry.get('time', time.time())),
                    'client_ip': entry.get('client', ''),
                    'domain': entry.get('question', {}).get('name', '') if isinstance(entry.get('question'), dict) else '',
                    'qtype': entry.get('question', {}).get('type', '') if isinstance(entry.get('question'), dict) else None,
                    'status': entry.get('status', '').lower() if entry.get('status') else None,
                    'upstream': entry.get('upstream', '') if entry.get('upstream') else None
                }
                
                if event['client_ip'] and event['domain']:
                    events.append(event)
            
            return events
    except Exception as e:
        print(f"Error fetching AdGuard API: {e}", file=__import__('sys').stderr)
        return []


def parse_adguard_file_line(line: str) -> Optional[Dict]:
    """Parse a single line from AdGuard query log file.
    
    Returns dict with keys: ts, client_ip, domain, qtype, status, upstream or None if invalid
    """
    try:
        # Try JSON format first
        entry = json.loads(line.strip())
        
        event = {
            'ts': int(entry.get('time', time.time())),
            'client_ip': entry.get('client', ''),
            'domain': entry.get('question', {}).get('name', '') if isinstance(entry.get('question'), dict) else '',
            'qtype': entry.get('question', {}).get('type', '') if isinstance(entry.get('question'), dict) else None,
            'status': entry.get('status', '').lower() if entry.get('status') else None,
            'upstream': entry.get('upstream', '') if entry.get('upstream') else None
        }
        
        if event['client_ip'] and event['domain']:
            return event
    except (json.JSONDecodeError, ValueError, KeyError):
        # Not JSON or invalid format - skip
        pass
    
    return None


def read_adguard_file(file_path: str, last_offset: int = 0) -> Tuple[List[Dict], int]:
    """Read new entries from AdGuard query log file.
    
    Returns (events, new_offset)
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Seek to last offset
            f.seek(last_offset)
            
            events = []
            new_offset = last_offset
            
            # Read new lines
            for line in f:
                event = parse_adguard_file_line(line)
                if event:
                    events.append(event)
                new_offset = f.tell()
            
            return events, new_offset
    except FileNotFoundError:
        return [], last_offset
    except Exception as e:
        print(f"Error reading AdGuard file: {e}", file=__import__('sys').stderr)
        return [], last_offset

