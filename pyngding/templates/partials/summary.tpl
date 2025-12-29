<div class="summary-cards">
    <div class="card">
        <h3>Hosts Up</h3>
        <p class="stat-value">{{stats.get('up_count', 0)}}</p>
    </div>
    <div class="card">
        <h3>Hosts Down</h3>
        <p class="stat-value">{{stats.get('down_count', 0)}}</p>
    </div>
    <div class="card">
        <h3>Total Hosts</h3>
        <p class="stat-value">{{stats.get('total_hosts', 0)}}</p>
    </div>
    <div class="card">
        <h3>Missing</h3>
        <p class="stat-value">{{stats.get('missing_count', 0)}}</p>
    </div>
    <div class="card">
        <h3>Last Scan</h3>
        <p class="stat-value">
            % if stats.get('last_scan_ts'):
                {{!time.strftime('%H:%M:%S', time.localtime(stats['last_scan_ts']))}}
            % else:
                Never
            % end
        </p>
    </div>
    % if ipv6_enabled:
    <div class="card">
        <h3>IPv6 Neighbors (1h)</h3>
        <p class="stat-value">{{ipv6_count}}</p>
    </div>
    % end
</div>

