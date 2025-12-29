% if enabled:
<div class="dns-summary">
    <h4>DNS Activity for {{ip}}</h4>
    
    <div class="dns-stats">
        <strong>Last 24h:</strong>
        <ul>
            <li>Total queries: {{summary['stats']['total_queries']}}</li>
            <li>Blocked: {{summary['stats']['blocked_queries']}}</li>
            <li>Unique domains: {{summary['stats']['unique_domains']}}</li>
        </ul>
    </div>
    
    <div class="dns-top-domains">
        <h5>Top Domains (24h)</h5>
        <ul>
            % for domain in summary['top_domains']:
            <li>{{domain['domain']}} ({{domain['count']}} queries)</li>
            % end
            % if not summary['top_domains']:
            <li>No DNS activity</li>
            % end
        </ul>
    </div>
    
    <div class="dns-recent">
        <h5>Recent Queries</h5>
        <ul>
            % import time
            % for domain in summary['recent_domains'][:10]:
            <li>
                {{domain['domain']}}
                % if domain['status']:
                <span class="dns-status dns-{{domain['status']}}">{{domain['status']}}</span>
                % end
                <small>({{!time.strftime('%H:%M:%S', time.localtime(domain['ts']))}})</small>
            </li>
            % end
            % if not summary['recent_domains']:
            <li>No recent queries</li>
            % end
        </ul>
    </div>
</div>
% else:
<div class="dns-summary">
    <p>AdGuard integration is disabled. Enable it in Settings to see DNS activity.</p>
</div>
% end

<style>
.dns-summary {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 4px;
    margin-top: 1rem;
}

.dns-stats ul, .dns-top-domains ul, .dns-recent ul {
    list-style: none;
    padding-left: 0;
}

.dns-stats li, .dns-top-domains li, .dns-recent li {
    padding: 0.25rem 0;
}

.dns-status {
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
    font-size: 0.8rem;
    margin-left: 0.5rem;
}

.dns-status.dns-blocked {
    background-color: #f8d7da;
    color: #721c24;
}

.dns-status.dns-allowed {
    background-color: #d4edda;
    color: #155724;
}

small {
    color: #666;
    margin-left: 0.5rem;
}
</style>

