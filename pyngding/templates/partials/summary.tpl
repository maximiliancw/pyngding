<div class="grid">
    <article>
        <header>
            <h3>Hosts Up</h3>
        </header>
        <p style="font-size: 2rem; font-weight: bold; margin: 0;">{{stats.get('up_count', 0)}}</p>
    </article>
    <article>
        <header>
            <h3>Hosts Down</h3>
        </header>
        <p style="font-size: 2rem; font-weight: bold; margin: 0;">{{stats.get('down_count', 0)}}</p>
    </article>
    <article>
        <header>
            <h3>Total Hosts</h3>
        </header>
        <p style="font-size: 2rem; font-weight: bold; margin: 0;">{{stats.get('total_hosts', 0)}}</p>
    </article>
    <article>
        <header>
            <h3>Missing</h3>
        </header>
        <p style="font-size: 2rem; font-weight: bold; margin: 0;">{{stats.get('missing_count', 0)}}</p>
    </article>
    <article>
        <header>
            <h3>Last Scan</h3>
        </header>
        <p style="font-size: 2rem; font-weight: bold; margin: 0;">
            % if stats.get('last_scan_ts'):
                {{!time.strftime('%H:%M:%S', time.localtime(stats['last_scan_ts']))}}
            % else:
                Never
            % end
        </p>
    </article>
    % if ipv6_enabled:
    <article>
        <header>
            <h3>IPv6 Neighbors (1h)</h3>
        </header>
        <p style="font-size: 2rem; font-weight: bold; margin: 0;">{{ipv6_count}}</p>
    </article>
    % end
</div>

