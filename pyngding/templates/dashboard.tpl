% rebase('layout.tpl', title='Dashboard')
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

