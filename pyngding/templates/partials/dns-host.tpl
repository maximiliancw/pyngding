% if enabled:
<article style="margin-top: 1rem;">
    <header>
        <h4>DNS Activity for {{ip}}</h4>
    </header>
    
    <section>
        <strong>Last 24h:</strong>
        <ul>
            <li>Total queries: {{summary['stats']['total_queries']}}</li>
            <li>Blocked: {{summary['stats']['blocked_queries']}}</li>
            <li>Unique domains: {{summary['stats']['unique_domains']}}</li>
        </ul>
    </section>
    
    <section>
        <h5>Top Domains (24h)</h5>
        <ul>
            % for domain in summary['top_domains']:
            <li>{{domain['domain']}} ({{domain['count']}} queries)</li>
            % end
            % if not summary['top_domains']:
            <li>No DNS activity</li>
            % end
        </ul>
    </section>
    
    <section>
        <h5>Recent Queries</h5>
        <ul>
            % import time
            % for domain in summary['recent_domains'][:10]:
            <li>
                {{domain['domain']}}
                % if domain['status']:
                <mark style="padding: 0.1rem 0.4rem; border-radius: 0.25rem; margin-left: 0.5rem; font-size: 0.8rem; background-color: {{'var(--pico-del-color)' if domain['status'] == 'blocked' else 'var(--pico-ins-color)'}}; color: var(--pico-background-color);">{{domain['status']}}</mark>
                % end
                <small>({{!time.strftime('%H:%M:%S', time.localtime(domain['ts']))}})</small>
            </li>
            % end
            % if not summary['recent_domains']:
            <li>No recent queries</li>
            % end
        </ul>
    </section>
</article>
% else:
<article style="margin-top: 1rem;">
    <p>AdGuard integration is disabled. Enable it in Settings to see DNS activity.</p>
</article>
% end


