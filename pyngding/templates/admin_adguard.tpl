% rebase('layout.tpl', title='AdGuard Status', auth_enabled=auth_enabled)
<div class="admin-adguard-page">
    <h2>AdGuard Integration Status</h2>
    
    % if not adguard_enabled:
    <div class="alert alert-error">
        AdGuard integration is disabled. Enable it in Settings.
    </div>
    % else:
    <div class="adguard-stats">
        <div class="stat-card">
            <h3>Total DNS Events</h3>
            <p class="stat-value">{{total_events}}</p>
        </div>
        <div class="stat-card">
            <h3>Events (Last Hour)</h3>
            <p class="stat-value">{{recent_events}}</p>
        </div>
        <div class="stat-card">
            <h3>Last Ingest</h3>
            <p class="stat-value">
                % if state['last_seen_ts']:
                    % import time
                    {{!time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(state['last_seen_ts']))}}
                % else:
                    Never
                % end
            </p>
        </div>
    </div>
    
    <div class="adguard-info">
        <h3>Ingestion State</h3>
        <ul>
            <li>Mode: {{get_ui_setting_helper(db_path, 'adguard_mode', 'api')}}</li>
            % if state['last_seen_ts']:
            <li>Last seen timestamp: {{state['last_seen_ts']}}</li>
            % end
            % if state['last_offset']:
            <li>File offset: {{state['last_offset']}}</li>
            % end
        </ul>
    </div>
    % end
</div>

<style>
.adguard-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-card h3 {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 0.5rem;
}

.stat-card .stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: #2c3e50;
}

.adguard-info {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.adguard-info ul {
    list-style: none;
    padding-left: 0;
}

.adguard-info li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #dee2e6;
}
</style>

