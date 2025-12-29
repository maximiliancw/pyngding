% rebase('layout.tpl', title='Dashboard', auth_enabled=auth_enabled)
<div class="dashboard">
    <h2>Dashboard</h2>
    
    <div id="summary" hx-get="/partials/summary" hx-trigger="every 10s" hx-swap="outerHTML">
        % include('partials/summary.tpl', stats=stats)
    </div>
    
    <div class="chart-container">
        <h3>Hosts Up Over Time</h3>
        <canvas id="chart"></canvas>
    </div>
    
    <div id="recent-changes" hx-get="/partials/recent-changes" hx-trigger="every 10s" hx-swap="outerHTML">
        % include('partials/recent-changes.tpl', runs=stats.get('recent_runs', []))
    </div>
    
    % if auth_enabled and new_hosts:
    <div class="new-devices">
        <h3>New/Unknown Devices</h3>
        <table>
            <thead>
                <tr>
                    <th>IP</th>
                    <th>Hostname</th>
                    <th>MAC</th>
                    <th>Last Seen</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                % import time
                % for host in new_hosts:
                <tr>
                    <td>{{host['ip']}}</td>
                    <td>{{host['hostname'] or '-'}}</td>
                    <td>{{host['mac'] or '-'}}</td>
                    <td>{{!time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(host['last_seen_ts']))}}</td>
                    <td>
                        <form method="POST" action="/admin/hosts/{{host['ip']}}/update" style="display: inline;">
                            <input type="hidden" name="is_safe" value="true">
                            <button type="submit" class="btn-mark-safe">Mark Safe</button>
                        </form>
                    </td>
                </tr>
                % end
            </tbody>
        </table>
    </div>
    % end
</div>

<script>
    const chartData = {{!chart_data_json}};
    const ctx = document.getElementById('chart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Hosts Up',
                data: chartData.up_counts,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
</script>

