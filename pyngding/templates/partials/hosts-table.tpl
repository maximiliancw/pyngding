<table class="hosts-table">
    <thead>
        <tr>
            <th>IP</th>
            <th>Hostname</th>
            <th>MAC</th>
            <th>Vendor</th>
            <th>Status</th>
            <th>RTT (ms)</th>
            <th>Last Seen</th>
        </tr>
    </thead>
    <tbody>
        % import time
        % for host in hosts:
        <tr class="status-{{host['last_status']}}">
            <td>
                {{host['ip']}}
                <button onclick="toggleDNS('{{host['ip']}}')" class="btn-dns-toggle" title="Show DNS activity">DNS</button>
            </td>
            <td>{{host['hostname'] or '-'}}</td>
            <td>{{host['mac'] or '-'}}</td>
            <td>{{host['vendor'] or '-'}}</td>
            <td><span class="status-badge status-{{host['last_status']}}">{{host['last_status']}}</span></td>
            <td>{{host['last_rtt_ms'] or '-'}}</td>
            <td>{{!time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(host['last_seen_ts']))}}</td>
        </tr>
        <tr id="dns-{{host['ip']}}" style="display: none;">
            <td colspan="7">
                <div hx-get="/partials/dns-host/{{host['ip']}}" hx-trigger="load" hx-swap="innerHTML">
                    Loading DNS data...
                </div>
            </td>
        </tr>
        % end
        % if not hosts:
        <tr>
            <td colspan="7" class="no-results">No hosts found</td>
        </tr>
        % end
    </tbody>
</table>

<script>
function toggleDNS(ip) {
    const row = document.getElementById('dns-' + ip);
    if (row.style.display === 'none') {
        row.style.display = '';
        // Trigger HTMX load if not already loaded
        const div = row.querySelector('div');
        if (div && !div.hasAttribute('data-loaded')) {
            div.setAttribute('data-loaded', 'true');
            htmx.trigger(div, 'load');
        }
    } else {
        row.style.display = 'none';
    }
}
</script>

<style>
.btn-dns-toggle {
    padding: 0.2rem 0.5rem;
    font-size: 0.8rem;
    background-color: #17a2b8;
    color: white;
    border: none;
    border-radius: 3px;
    cursor: pointer;
    margin-left: 0.5rem;
}

.btn-dns-toggle:hover {
    background-color: #138496;
}
</style>

