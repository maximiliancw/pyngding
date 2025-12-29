% rebase('layout.tpl', title='Settings', auth_enabled=auth_enabled)
<article>
    <header>
        <h1>Settings</h1>
    </header>
    
    % if errors:
    <article style="background-color: var(--pico-del-color); color: var(--pico-background-color);">
        <strong>Errors:</strong>
        <ul>
            % for error in errors:
            <li>{{error}}</li>
            % end
        </ul>
    </article>
    % end
    
    % if request.query.get('updated'):
    <article style="background-color: var(--pico-ins-color); color: var(--pico-background-color);">
        Settings updated successfully!
    </article>
    % end
    
    % if request.query.get('notify_test'):
    % notify_channel = request.query.get('notify_test')
    % notify_success = request.query.get('success') == 'true'
    % if notify_success:
    <article style="background-color: var(--pico-ins-color); color: var(--pico-background-color);">
        Test notification sent successfully via {{notify_channel}}!
    </article>
    % else:
    <article style="background-color: var(--pico-del-color); color: var(--pico-background-color);">
        Test notification failed via {{notify_channel}}. Check your settings.
    </article>
    % end
    % end
    
    <form method="POST" action="/admin/settings">
        <article>
            <header>
                <h2>General/UI</h2>
            </header>
            <label for="reverse_dns">
                <input type="checkbox" name="reverse_dns" id="reverse_dns" value="true" {{'checked' if settings.get('reverse_dns') == 'true' else ''}}>
                Enable Reverse DNS Lookup
            </label>
            <label for="missing_threshold_minutes">Missing Threshold (minutes):</label>
            <input type="number" name="missing_threshold_minutes" id="missing_threshold_minutes" 
                   value="{{settings.get('missing_threshold_minutes', '10')}}" min="1">
            <label for="chart_window_runs">Chart Window (runs):</label>
            <input type="number" name="chart_window_runs" id="chart_window_runs" 
                   value="{{settings.get('chart_window_runs', '200')}}" min="10" max="1000">
            <label for="ui_refresh_seconds">UI Refresh Interval (seconds):</label>
            <input type="number" name="ui_refresh_seconds" id="ui_refresh_seconds" 
                   value="{{settings.get('ui_refresh_seconds', '10')}}" min="1">
            <label for="metrics_enabled">
                <input type="checkbox" name="metrics_enabled" id="metrics_enabled" value="true" {{'checked' if settings.get('metrics_enabled') == 'true' else ''}}>
                Enable Metrics Endpoint
            </label>
        </article>
        
        <article>
            <header>
                <h2>API/Home Assistant</h2>
            </header>
            <label for="api_enabled">
                <input type="checkbox" name="api_enabled" id="api_enabled" value="true" {{'checked' if settings.get('api_enabled') == 'true' else ''}}>
                Enable API
            </label>
            <label for="api_rate_limit_rps">API Rate Limit (requests/second):</label>
            <input type="number" name="api_rate_limit_rps" id="api_rate_limit_rps" 
                   value="{{settings.get('api_rate_limit_rps', '5')}}" min="1" max="100">
        </article>
        
        <article>
            <header>
                <h2>Retention</h2>
            </header>
            <label for="raw_observation_retention_days">Raw Observations (days, 0=keep forever):</label>
            <input type="number" name="raw_observation_retention_days" id="raw_observation_retention_days" 
                   value="{{settings.get('raw_observation_retention_days', '90')}}" min="0">
            <label for="dns_event_retention_days">DNS Events (days):</label>
            <input type="number" name="dns_event_retention_days" id="dns_event_retention_days" 
                   value="{{settings.get('dns_event_retention_days', '7')}}" min="0">
            <label for="scan_run_retention_days">Scan Runs (days, 0=keep forever):</label>
            <input type="number" name="scan_run_retention_days" id="scan_run_retention_days" 
                   value="{{settings.get('scan_run_retention_days', '365')}}" min="0">
        </article>
        
        <article>
            <header>
                <h2>Notifications</h2>
            </header>
            <label for="notify_enabled">
                <input type="checkbox" name="notify_enabled" id="notify_enabled" value="true" {{'checked' if settings.get('notify_enabled') == 'true' else ''}}>
                Enable Notifications
            </label>
            <label for="notify_on_new_host">
                <input type="checkbox" name="notify_on_new_host" id="notify_on_new_host" value="true" {{'checked' if settings.get('notify_on_new_host') == 'true' else ''}}>
                Notify on New Host
            </label>
            <label for="notify_on_host_gone">
                <input type="checkbox" name="notify_on_host_gone" id="notify_on_host_gone" value="true" {{'checked' if settings.get('notify_on_host_gone') == 'true' else ''}}>
                Notify on Host Gone
            </label>
            <label for="notify_on_ip_mac_change">
                <input type="checkbox" name="notify_on_ip_mac_change" id="notify_on_ip_mac_change" value="true" {{'checked' if settings.get('notify_on_ip_mac_change') == 'true' else ''}}>
                Notify on IP/MAC Change
            </label>
            <label for="notify_on_duplicate_ip">
                <input type="checkbox" name="notify_on_duplicate_ip" id="notify_on_duplicate_ip" value="true" {{'checked' if settings.get('notify_on_duplicate_ip') == 'true' else ''}}>
                Notify on Duplicate IP
            </label>
            <label for="notify_on_dns_burst">
                <input type="checkbox" name="notify_on_dns_burst" id="notify_on_dns_burst" value="true" {{'checked' if settings.get('notify_on_dns_burst') == 'true' else ''}}>
                Notify on DNS Burst
            </label>
        </article>
        
        <article>
            <header>
                <h2>Webhook</h2>
            </header>
            <label for="webhook_enabled">
                <input type="checkbox" name="webhook_enabled" id="webhook_enabled" value="true" {{'checked' if settings.get('webhook_enabled') == 'true' else ''}}>
                Enable Webhook
            </label>
            <label for="webhook_url">Webhook URL:</label>
            <input type="url" name="webhook_url" id="webhook_url" 
                   value="{{settings.get('webhook_url', '')}}" placeholder="https://example.com/webhook">
            <label for="webhook_secret">Webhook Secret (optional):</label>
            <input type="text" name="webhook_secret" id="webhook_secret" 
                   value="{{settings.get('webhook_secret', '')}}">
            <form method="POST" action="/admin/notify/test" style="display: inline;">
                <input type="hidden" name="channel" value="webhook">
                <button type="submit" class="secondary">Test Webhook</button>
            </form>
        </article>
        
        <article>
            <header>
                <h2>Home Assistant Webhook</h2>
            </header>
            <label for="ha_webhook_enabled">
                <input type="checkbox" name="ha_webhook_enabled" id="ha_webhook_enabled" value="true" {{'checked' if settings.get('ha_webhook_enabled') == 'true' else ''}}>
                Enable HA Webhook
            </label>
            <label for="ha_webhook_url">HA Webhook URL:</label>
            <input type="url" name="ha_webhook_url" id="ha_webhook_url" 
                   value="{{settings.get('ha_webhook_url', '')}}" placeholder="https://homeassistant.local:8123/api/webhook/...">
            <form method="POST" action="/admin/notify/test" style="display: inline;">
                <input type="hidden" name="channel" value="ha_webhook">
                <button type="submit" class="secondary">Test HA Webhook</button>
            </form>
        </article>
        
        <article>
            <header>
                <h2>ntfy.sh</h2>
            </header>
            <label for="ntfy_enabled">
                <input type="checkbox" name="ntfy_enabled" id="ntfy_enabled" value="true" {{'checked' if settings.get('ntfy_enabled') == 'true' else ''}}>
                Enable ntfy
            </label>
            <label for="ntfy_base_url">Base URL:</label>
            <input type="url" name="ntfy_base_url" id="ntfy_base_url" 
                   value="{{settings.get('ntfy_base_url', 'https://ntfy.sh')}}">
            <label for="ntfy_topic">Topic (required if enabled):</label>
            <input type="text" name="ntfy_topic" id="ntfy_topic" 
                   value="{{settings.get('ntfy_topic', '')}}">
            <form method="POST" action="/admin/notify/test" style="display: inline;">
                <input type="hidden" name="channel" value="ntfy">
                <button type="submit" class="secondary">Test ntfy</button>
            </form>
        </article>
        
        <article>
            <header>
                <h2>Device Inventory</h2>
            </header>
            <label for="ipv6_passive_enabled">
                <input type="checkbox" name="ipv6_passive_enabled" id="ipv6_passive_enabled" value="true" {{'checked' if settings.get('ipv6_passive_enabled') == 'true' else ''}}>
                Enable IPv6 Passive Neighbor Collection
            </label>
            <label for="oui_lookup_enabled">
                <input type="checkbox" name="oui_lookup_enabled" id="oui_lookup_enabled" value="true" {{'checked' if settings.get('oui_lookup_enabled') == 'true' else ''}}>
                Enable OUI Vendor Lookup
            </label>
            <label for="oui_file_path">OUI File Path:</label>
            <input type="text" name="oui_file_path" id="oui_file_path" 
                   value="{{settings.get('oui_file_path', '')}}" placeholder="/data/oui.txt">
        </article>
        
        <button type="submit">Save Settings</button>
    </form>
</article>


