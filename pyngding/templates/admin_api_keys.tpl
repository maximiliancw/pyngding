% rebase('layout.tpl', title='API Keys', auth_enabled=auth_enabled)
<article>
    <header>
        <h1>API Keys</h1>
        <p>Manage API keys for Home Assistant integration.</p>
    </header>
    
    % if new_key:
    <article style="background-color: var(--pico-ins-color); color: var(--pico-background-color);">
        <strong>New API Key Created!</strong><br>
        <strong>Name:</strong> {{new_key['name']}}<br>
        <strong>Key:</strong> <code style="background: rgba(0,0,0,0.2); padding: 0.5rem; display: block; margin: 0.5rem 0; word-break: break-all;">{{new_key['key']}}</code>
        <strong>⚠️ Save this key now - it will not be shown again!</strong>
    </article>
    % end
    
    % if error:
    <article style="background-color: var(--pico-del-color); color: var(--pico-background-color);">
        {{error}}
    </article>
    % end
    
    <article>
        <header>
            <h2>Create New API Key</h2>
        </header>
        <form method="POST" action="/admin/api-keys">
            <label for="name">Name:</label>
            <input type="text" name="name" id="name" required placeholder="e.g., Home Assistant">
            <button type="submit">Create API Key</button>
        </form>
    </article>
    
    <article>
        <header>
            <h2>Existing API Keys</h2>
        </header>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Prefix</th>
                    <th>Created</th>
                    <th>Last Used</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                % import time
                % for key in api_keys:
                <tr>
                    <td>{{key['name']}}</td>
                    <td><code>{{key['key_prefix']}}...</code></td>
                    <td>{{!time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(key['created_ts']))}}</td>
                    <td>
                        % if key['last_used_ts']:
                        {{!time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(key['last_used_ts']))}}
                        % else:
                        Never
                        % end
                    </td>
                    <td>
                        % if key['is_enabled']:
                        <mark style="background-color: var(--pico-ins-color); color: var(--pico-background-color); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">Enabled</mark>
                        % else:
                        <mark style="background-color: var(--pico-del-color); color: var(--pico-background-color); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">Disabled</mark>
                        % end
                    </td>
                    <td>
                        <form method="POST" action="/admin/api-keys/{{key['id']}}/toggle" style="display: inline;">
                            <button type="submit" class="secondary" style="padding: 0.25rem 0.75rem; font-size: 0.9rem;">
                                {{'Disable' if key['is_enabled'] else 'Enable'}}
                            </button>
                        </form>
                        <form method="POST" action="/admin/api-keys/{{key['id']}}/delete" style="display: inline;" 
                              onsubmit="return confirm('Are you sure you want to delete this API key?');">
                            <button type="submit" class="contrast" style="padding: 0.25rem 0.75rem; font-size: 0.9rem;">Delete</button>
                        </form>
                    </td>
                </tr>
                % end
                % if not api_keys:
                <tr>
                    <td colspan="6" style="text-align: center; padding: 2rem; color: var(--pico-muted-color);">No API keys created yet</td>
                </tr>
                % end
            </tbody>
        </table>
    </article>
</article>


