<table>
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
        <tr>
            <td>
                {{host['ip']}}
                <button onclick="toggleDNS('{{host['ip']}}')" class="secondary" style="margin-left: 0.5rem; padding: 0.2rem 0.5rem; font-size: 0.8rem;" title="Show DNS activity">DNS</button>
            </td>
            <td>{{host['hostname'] or '-'}}</td>
            <td>{{host['mac'] or '-'}}</td>
            <td>{{host['vendor'] or '-'}}</td>
            <td>
                % if host['last_status'] == 'up':
                <mark style="background-color: var(--pico-ins-color); color: var(--pico-background-color); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{{host['last_status']}}</mark>
                % else:
                <mark style="background-color: var(--pico-del-color); color: var(--pico-background-color); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{{host['last_status']}}</mark>
                % end
            </td>
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
            <td colspan="7" style="text-align: center; padding: 2rem; color: var(--pico-muted-color);">No hosts found</td>
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

