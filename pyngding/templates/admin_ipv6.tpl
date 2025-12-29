% rebase('layout.tpl', title='IPv6 Neighbors', auth_enabled=auth_enabled)
<article>
    <header>
        <h1>IPv6 Neighbors</h1>
    </header>
    
    % if not ipv6_enabled:
    <article style="background-color: var(--pico-del-color); color: var(--pico-background-color);">
        IPv6 passive neighbor collection is disabled. Enable it in Settings.
    </article>
    % else:
    <p>Showing IPv6 neighbors seen in the last 24 hours.</p>
    
    <table>
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
                <td colspan="4" style="text-align: center; padding: 2rem; color: var(--pico-muted-color);">No IPv6 neighbors found in the last 24 hours</td>
            </tr>
            % end
        </tbody>
    </table>
    % end
</article>


