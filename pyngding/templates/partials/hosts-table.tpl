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
            <td>{{host['ip']}}</td>
            <td>{{host['hostname'] or '-'}}</td>
            <td>{{host['mac'] or '-'}}</td>
            <td>{{host['vendor'] or '-'}}</td>
            <td><span class="status-badge status-{{host['last_status']}}">{{host['last_status']}}</span></td>
            <td>{{host['last_rtt_ms'] or '-'}}</td>
            <td>{{!time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(host['last_seen_ts']))}}</td>
        </tr>
        % end
        % if not hosts:
        <tr>
            <td colspan="7" class="no-results">No hosts found</td>
        </tr>
        % end
    </tbody>
</table>

