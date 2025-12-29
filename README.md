# pyngding

A lightweight LAN presence scanner and dashboard for network administrators, designed to complement AdGuard Home and Unbound.

## Features

- **IPv4 Network Scanning**: Periodic scanning of configured IP ranges using ping
- **MAC Address Detection**: Automatic MAC address enrichment via `ip neigh show`
- **Reverse DNS Lookup**: Optional reverse DNS resolution for discovered hosts
- **Web Dashboard**: Modern web UI with HTMX auto-refresh and Chart.js visualizations
- **Home Assistant Integration**: RESTful API endpoints for Home Assistant automation
- **AdGuard Home Integration**: DNS query log ingestion (API or file mode) with per-host DNS summaries
- **Notifications**: Webhook, Home Assistant webhook, and ntfy.sh support
- **Device Inventory**: Label, tag, and mark devices as safe
- **OUI Vendor Lookup**: MAC address to vendor name mapping
- **IPv6 Passive Neighbors**: IPv6 neighbor discovery (no active scanning)
- **Data Retention**: Configurable retention policies with automatic cleanup
- **Prometheus Metrics**: Built-in metrics endpoint for monitoring

## Requirements

- Python 3.11+
- Linux (for `ping` and `ip` commands)
- Bottle (only external dependency)

## Quick Start

### Docker (Recommended)

1. Clone the repository:
```bash
git clone <repo-url>
cd pyngding-main
```

2. Create data directory and config:
```bash
mkdir -p docker/data
cd docker/data
pyngding init-config --path config.ini
```

3. Set up authentication (optional):
```bash
pyngding hash-password "your-password"
# Copy the output and paste it into config.ini as auth.password_hash
```

4. Edit `config.ini` and set your scan targets:
```ini
[pyngding]
scan_targets = 192.168.1.0/24
```

5. Start with docker-compose:
```bash
cd ..
docker-compose up -d
```

6. Access the web UI at `http://localhost:8080`

### Bare Metal Installation

1. Install dependencies:
```bash
pip install -e .
```

2. Initialize config:
```bash
pyngding init-config --path config.ini
```

3. Configure authentication and scan targets in `config.ini`

4. Run:
```bash
pyngding serve --config config.ini
```

## Configuration

### Critical Settings (config.ini only)

- `bind_host`: Web server bind address (default: 0.0.0.0)
- `bind_port`: Web server port (default: 8080)
- `db_path`: SQLite database path (default: /data/pyngding.sqlite)
- `scan_targets`: Comma-separated CIDR ranges or IP ranges (e.g., `192.168.1.0/24,10.0.0.1-10.0.0.50`)
- `scan_interval_seconds`: Scan frequency (default: 60)
- `ping_timeout_seconds`: Ping timeout (default: 1.0)
- `ping_count`: Number of ping packets (default: 1)
- `max_workers`: Concurrent scan workers (default: 32, max: 64)
- `auth.enabled`: Enable BasicAuth (default: false)
- `auth.username`: Admin username (default: admin)
- `auth.password_hash`: PBKDF2 password hash (use `pyngding hash-password`)

### UI-Managed Settings

When authentication is enabled, most settings can be managed via the Admin UI:

- **General/UI**: Reverse DNS, missing threshold, chart window, UI refresh interval
- **API/HA**: API enable/disable, rate limiting
- **Retention**: Observation retention, DNS event retention, scan run retention
- **AdGuard**: Integration mode (API/file), URLs, credentials
- **Notifications**: Webhook, HA webhook, ntfy.sh configuration
- **Device Inventory**: IPv6 passive collection, OUI lookup

## Home Assistant Integration

1. Enable authentication in `config.ini`
2. Access Admin UI → API Keys
3. Create a new API key (save it immediately - it's shown only once)
4. Use the API key in Home Assistant REST sensors:

```yaml
sensor:
  - platform: rest
    name: pyngding_hosts_up
    resource: http://pyngding:8080/api/ha/summary
    headers:
      X-API-Key: your-api-key-here
    value_template: '{{ value_json.up_count }}'
```

## AdGuard Home Integration

### API Mode

1. Enable AdGuard integration in Settings
2. Set `adguard_mode = api`
3. Configure `adguard_base_url` (e.g., `http://adguardhome:3000`)
4. Optionally set `adguard_username` and `adguard_password`

### File Mode

1. Enable AdGuard integration in Settings
2. Set `adguard_mode = file`
3. Configure `adguard_querylog_path` (e.g., `/adguard/data/querylog.json`)
4. Mount AdGuard data directory read-only into container

## Notifications

### Webhook

Configure a generic webhook URL in Settings. Payload includes:
- `event_type`: new_host, host_gone, ip_mac_change, etc.
- `ip`, `mac`, `hostname`, `vendor`
- `label`, `is_safe`, `tags`
- `ts`: Unix timestamp

### Home Assistant Webhook

Set `ha_webhook_url` to your Home Assistant webhook endpoint. Events are sent as Home Assistant events.

### ntfy.sh

Configure ntfy topic and optional authentication. Supports:
- Basic auth
- Bearer token auth
- Custom priority and tags

## OUI Vendor Lookup

1. Download an OUI file (e.g., from IEEE)
2. Import it:
```bash
pyngding oui import --path /path/to/oui.txt
```
3. Enable OUI lookup in Settings
4. Set `oui_file_path` to the file location

## ARMv6 Support (Raspberry Pi 1B)

For ARMv6 devices, modify `docker/Dockerfile`:

```dockerfile
FROM arm32v6/python:3.11-slim
```

Or use the build arg in docker-compose.yml (see comments).

## API Endpoints

All API endpoints require authentication enabled and a valid API key via `X-API-Key` header.

- `GET /api/health` - Health check
- `GET /api/ha/summary` - Scan statistics
- `GET /api/ha/hosts?status=up|down` - Host list
- `GET /api/ha/alerts/recent` - Recent alerts (placeholder)

## Metrics

Prometheus metrics available at `/metrics` (requires authentication):

- `pyngding_hosts_up` (gauge)
- `pyngding_hosts_down` (gauge)
- `pyngding_hosts_total` (gauge)
- `pyngding_hosts_missing` (gauge)
- `pyngding_scan_runs_total` (counter)
- `pyngding_observations_total` (counter)
- `pyngding_dns_events_total` (counter)
- `pyngding_last_scan_timestamp` (gauge)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

