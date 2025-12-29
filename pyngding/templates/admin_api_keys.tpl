% rebase('layout.tpl', title='API Keys', auth_enabled=auth_enabled)
<div class="admin-api-keys-page">
    <h2>API Keys</h2>
    <p>Manage API keys for Home Assistant integration.</p>
    
    % if new_key:
    <div class="alert alert-success">
        <strong>New API Key Created!</strong><br>
        <strong>Name:</strong> {{new_key['name']}}<br>
        <strong>Key:</strong> <code style="background: #f0f0f0; padding: 0.5rem; display: block; margin: 0.5rem 0; word-break: break-all;">{{new_key['key']}}</code>
        <strong style="color: #721c24;">⚠️ Save this key now - it will not be shown again!</strong>
    </div>
    % end
    
    % if error:
    <div class="alert alert-error">
        {{error}}
    </div>
    % end
    
    <div class="create-key-section">
        <h3>Create New API Key</h3>
        <form method="POST" action="/admin/api-keys">
            <div class="form-group">
                <label for="name">Name:</label>
                <input type="text" name="name" id="name" required placeholder="e.g., Home Assistant">
            </div>
            <button type="submit">Create API Key</button>
        </form>
    </div>
    
    <div class="keys-list">
        <h3>Existing API Keys</h3>
        <table class="hosts-table">
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
                        <span class="status-badge status-up">Enabled</span>
                        % else:
                        <span class="status-badge status-down">Disabled</span>
                        % end
                    </td>
                    <td>
                        <form method="POST" action="/admin/api-keys/{{key['id']}}/toggle" style="display: inline;">
                            <button type="submit" class="btn-small">
                                {{'Disable' if key['is_enabled'] else 'Enable'}}
                            </button>
                        </form>
                        <form method="POST" action="/admin/api-keys/{{key['id']}}/delete" style="display: inline;" 
                              onsubmit="return confirm('Are you sure you want to delete this API key?');">
                            <button type="submit" class="btn-small btn-danger">Delete</button>
                        </form>
                    </td>
                </tr>
                % end
                % if not api_keys:
                <tr>
                    <td colspan="6" class="no-results">No API keys created yet</td>
                </tr>
                % end
            </tbody>
        </table>
    </div>
</div>

<style>
.create-key-section {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.create-key-section h3 {
    margin-bottom: 1rem;
    color: #2c3e50;
}

.keys-list {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.keys-list h3 {
    margin-bottom: 1rem;
    color: #2c3e50;
}

.btn-small {
    padding: 0.25rem 0.75rem;
    font-size: 0.9rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 0.5rem;
}

.btn-small:not(.btn-danger) {
    background-color: #2c3e50;
    color: white;
}

.btn-danger {
    background-color: #dc3545;
    color: white;
}

.btn-small:hover {
    opacity: 0.9;
}

code {
    font-family: monospace;
    background-color: #f0f0f0;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
}
</style>

