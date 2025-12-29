% rebase('layout.tpl', title='IPv6 Neighbors', auth_enabled=auth_enabled)
<div class="admin-ipv6-page">
    <h2>IPv6 Neighbors</h2>
    
    % if not ipv6_enabled:
    <div class="alert alert-error">
        IPv6 passive neighbor collection is disabled. Enable it in Settings.
    </div>
    % else:
    <div class="ipv6-info">
        <p>Showing IPv6 neighbors seen in the last 24 hours.</p>
    </div>
    
    <table class="hosts-table">
        <thead>
            <tr>
                <th>IPv6 Address</th>
                <th>MAC Address</th>
                <th>State</th>
                <th>Last Seen</th>
            </tr>
        </thead>
        <tbody>
            % import time
            % for neighbor in neighbors:
            <tr>
                <td><code>{{neighbor['ip6']}}</code></td>
                <td>{{neighbor.get('mac') or '-'}}</td>
                <td>{{neighbor.get('state') or '-'}}</td>
                <td>
                    % if neighbor.get('last_seen'):
                    {{!time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(neighbor['last_seen']))}}
                    % else:
                    -
                    % end
                </td>
            </tr>
            % end
            % if not neighbors:
            <tr>
                <td colspan="4" class="no-results">No IPv6 neighbors found in the last 24 hours</td>
            </tr>
            % end
        </tbody>
    </table>
    % end
</div>

<style>
code {
    font-family: monospace;
    background-color: #f0f0f0;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
}
</style>

