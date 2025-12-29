% rebase('layout.tpl', title='AdGuard Status', auth_enabled=auth_enabled)
<article>
    <header>
        <h1>AdGuard Integration Status</h1>
    </header>
    
    % if not adguard_enabled:
    <article style="background-color: var(--pico-del-color); color: var(--pico-background-color);">
        AdGuard integration is disabled. Enable it in Settings.
    </article>
    % else:
    <div class="grid">
        <article>
            <header>
                <h3>Total DNS Events</h3>
            </header>
            <p style="font-size: 2rem; font-weight: bold; margin: 0;">{{total_events}}</p>
        </article>
        <article>
            <header>
                <h3>Events (Last Hour)</h3>
            </header>
            <p style="font-size: 2rem; font-weight: bold; margin: 0;">{{recent_events}}</p>
        </article>
        <article>
            <header>
                <h3>Last Ingest</h3>
            </header>
            <p style="font-size: 2rem; font-weight: bold; margin: 0;">
                % if state['last_seen_ts']:
                    % import time
                    {{!time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(state['last_seen_ts']))}}
                % else:
                    Never
                % end
            </p>
        </article>
    </div>
    
    <article>
        <header>
            <h2>Ingestion State</h2>
        </header>
        <ul>
            <li>Mode: {{get_ui_setting_helper(db_path, 'adguard_mode', 'api')}}</li>
            % if state['last_seen_ts']:
            <li>Last seen timestamp: {{state['last_seen_ts']}}</li>
            % end
            % if state['last_offset']:
            <li>File offset: {{state['last_offset']}}</li>
            % end
        </ul>
    </article>
    % end
</article>


