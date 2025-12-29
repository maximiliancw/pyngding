% rebase('layout.tpl', title='Settings', auth_enabled=auth_enabled)
<div class="admin-settings-page">
    <h2>Settings</h2>
    
    % if errors:
    <div class="alert alert-error">
        <strong>Errors:</strong>
        <ul>
            % for error in errors:
            <li>{{error}}</li>
            % end
        </ul>
    </div>
    % end
    
    % if request.query.get('updated'):
    <div class="alert alert-success">
        Settings updated successfully!
    </div>
    % end
    
    <form method="POST" action="/admin/settings">
        <div class="settings-section">
            <h3>General/UI</h3>
            <div class="form-group">
                <label for="reverse_dns">
                    <input type="checkbox" name="reverse_dns" id="reverse_dns" value="true" {{'checked' if settings.get('reverse_dns') == 'true' else ''}}>
                    Enable Reverse DNS Lookup
                </label>
            </div>
            <div class="form-group">
                <label for="missing_threshold_minutes">Missing Threshold (minutes):</label>
                <input type="number" name="missing_threshold_minutes" id="missing_threshold_minutes" 
                       value="{{settings.get('missing_threshold_minutes', '10')}}" min="1">
            </div>
            <div class="form-group">
                <label for="chart_window_runs">Chart Window (runs):</label>
                <input type="number" name="chart_window_runs" id="chart_window_runs" 
                       value="{{settings.get('chart_window_runs', '200')}}" min="10" max="1000">
            </div>
            <div class="form-group">
                <label for="ui_refresh_seconds">UI Refresh Interval (seconds):</label>
                <input type="number" name="ui_refresh_seconds" id="ui_refresh_seconds" 
                       value="{{settings.get('ui_refresh_seconds', '10')}}" min="1">
            </div>
            <div class="form-group">
                <label for="metrics_enabled">
                    <input type="checkbox" name="metrics_enabled" id="metrics_enabled" value="true" {{'checked' if settings.get('metrics_enabled') == 'true' else ''}}>
                    Enable Metrics Endpoint
                </label>
            </div>
        </div>
        
        <div class="settings-section">
            <h3>API/Home Assistant</h3>
            <div class="form-group">
                <label for="api_enabled">
                    <input type="checkbox" name="api_enabled" id="api_enabled" value="true" {{'checked' if settings.get('api_enabled') == 'true' else ''}}>
                    Enable API
                </label>
            </div>
            <div class="form-group">
                <label for="api_rate_limit_rps">API Rate Limit (requests/second):</label>
                <input type="number" name="api_rate_limit_rps" id="api_rate_limit_rps" 
                       value="{{settings.get('api_rate_limit_rps', '5')}}" min="1" max="100">
            </div>
        </div>
        
        <div class="settings-section">
            <h3>Retention</h3>
            <div class="form-group">
                <label for="raw_observation_retention_days">Raw Observations (days, 0=keep forever):</label>
                <input type="number" name="raw_observation_retention_days" id="raw_observation_retention_days" 
                       value="{{settings.get('raw_observation_retention_days', '90')}}" min="0">
            </div>
            <div class="form-group">
                <label for="dns_event_retention_days">DNS Events (days):</label>
                <input type="number" name="dns_event_retention_days" id="dns_event_retention_days" 
                       value="{{settings.get('dns_event_retention_days', '7')}}" min="0">
            </div>
            <div class="form-group">
                <label for="scan_run_retention_days">Scan Runs (days, 0=keep forever):</label>
                <input type="number" name="scan_run_retention_days" id="scan_run_retention_days" 
                       value="{{settings.get('scan_run_retention_days', '365')}}" min="0">
            </div>
        </div>
        
        <div class="settings-section">
            <h3>Notifications</h3>
            <div class="form-group">
                <label for="notify_enabled">
                    <input type="checkbox" name="notify_enabled" id="notify_enabled" value="true" {{'checked' if settings.get('notify_enabled') == 'true' else ''}}>
                    Enable Notifications
                </label>
            </div>
            <div class="form-group">
                <label for="notify_on_new_host">
                    <input type="checkbox" name="notify_on_new_host" id="notify_on_new_host" value="true" {{'checked' if settings.get('notify_on_new_host') == 'true' else ''}}>
                    Notify on New Host
                </label>
            </div>
            <div class="form-group">
                <label for="notify_on_host_gone">
                    <input type="checkbox" name="notify_on_host_gone" id="notify_on_host_gone" value="true" {{'checked' if settings.get('notify_on_host_gone') == 'true' else ''}}>
                    Notify on Host Gone
                </label>
            </div>
            <div class="form-group">
                <label for="notify_on_ip_mac_change">
                    <input type="checkbox" name="notify_on_ip_mac_change" id="notify_on_ip_mac_change" value="true" {{'checked' if settings.get('notify_on_ip_mac_change') == 'true' else ''}}>
                    Notify on IP/MAC Change
                </label>
            </div>
            <div class="form-group">
                <label for="notify_on_duplicate_ip">
                    <input type="checkbox" name="notify_on_duplicate_ip" id="notify_on_duplicate_ip" value="true" {{'checked' if settings.get('notify_on_duplicate_ip') == 'true' else ''}}>
                    Notify on Duplicate IP
                </label>
            </div>
            <div class="form-group">
                <label for="notify_on_dns_burst">
                    <input type="checkbox" name="notify_on_dns_burst" id="notify_on_dns_burst" value="true" {{'checked' if settings.get('notify_on_dns_burst') == 'true' else ''}}>
                    Notify on DNS Burst
                </label>
            </div>
        </div>
        
        <div class="settings-section">
            <h3>Webhook</h3>
            <div class="form-group">
                <label for="webhook_enabled">
                    <input type="checkbox" name="webhook_enabled" id="webhook_enabled" value="true" {{'checked' if settings.get('webhook_enabled') == 'true' else ''}}>
                    Enable Webhook
                </label>
            </div>
            <div class="form-group">
                <label for="webhook_url">Webhook URL:</label>
                <input type="url" name="webhook_url" id="webhook_url" 
                       value="{{settings.get('webhook_url', '')}}" placeholder="https://example.com/webhook">
            </div>
            <div class="form-group">
                <label for="webhook_secret">Webhook Secret (optional):</label>
                <input type="text" name="webhook_secret" id="webhook_secret" 
                       value="{{settings.get('webhook_secret', '')}}">
            </div>
        </div>
        
        <div class="settings-section">
            <h3>Home Assistant Webhook</h3>
            <div class="form-group">
                <label for="ha_webhook_enabled">
                    <input type="checkbox" name="ha_webhook_enabled" id="ha_webhook_enabled" value="true" {{'checked' if settings.get('ha_webhook_enabled') == 'true' else ''}}>
                    Enable HA Webhook
                </label>
            </div>
            <div class="form-group">
                <label for="ha_webhook_url">HA Webhook URL:</label>
                <input type="url" name="ha_webhook_url" id="ha_webhook_url" 
                       value="{{settings.get('ha_webhook_url', '')}}" placeholder="https://homeassistant.local:8123/api/webhook/...">
            </div>
        </div>
        
        <div class="settings-section">
            <h3>ntfy.sh</h3>
            <div class="form-group">
                <label for="ntfy_enabled">
                    <input type="checkbox" name="ntfy_enabled" id="ntfy_enabled" value="true" {{'checked' if settings.get('ntfy_enabled') == 'true' else ''}}>
                    Enable ntfy
                </label>
            </div>
            <div class="form-group">
                <label for="ntfy_base_url">Base URL:</label>
                <input type="url" name="ntfy_base_url" id="ntfy_base_url" 
                       value="{{settings.get('ntfy_base_url', 'https://ntfy.sh')}}">
            </div>
            <div class="form-group">
                <label for="ntfy_topic">Topic (required if enabled):</label>
                <input type="text" name="ntfy_topic" id="ntfy_topic" 
                       value="{{settings.get('ntfy_topic', '')}}">
            </div>
        </div>
        
        <div class="settings-section">
            <h3>Device Inventory</h3>
            <div class="form-group">
                <label for="ipv6_passive_enabled">
                    <input type="checkbox" name="ipv6_passive_enabled" id="ipv6_passive_enabled" value="true" {{'checked' if settings.get('ipv6_passive_enabled') == 'true' else ''}}>
                    Enable IPv6 Passive Neighbor Collection
                </label>
            </div>
            <div class="form-group">
                <label for="oui_lookup_enabled">
                    <input type="checkbox" name="oui_lookup_enabled" id="oui_lookup_enabled" value="true" {{'checked' if settings.get('oui_lookup_enabled') == 'true' else ''}}>
                    Enable OUI Vendor Lookup
                </label>
            </div>
            <div class="form-group">
                <label for="oui_file_path">OUI File Path:</label>
                <input type="text" name="oui_file_path" id="oui_file_path" 
                       value="{{settings.get('oui_file_path', '')}}" placeholder="/data/oui.txt">
            </div>
        </div>
        
        <div class="form-actions">
            <button type="submit">Save Settings</button>
        </div>
    </form>
</div>

<style>
.settings-section {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.settings-section h3 {
    margin-bottom: 1rem;
    color: #2c3e50;
    border-bottom: 2px solid #dee2e6;
    padding-bottom: 0.5rem;
}

.alert {
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
}

.alert-error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.alert-success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.alert ul {
    margin: 0.5rem 0 0 1.5rem;
}
</style>

