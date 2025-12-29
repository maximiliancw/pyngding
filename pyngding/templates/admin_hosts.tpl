% rebase('layout.tpl', title='Device Inventory', auth_enabled=auth_enabled)
<div class="admin-hosts-page">
    <h2>Device Inventory</h2>
    <p>Manage device labels, safety flags, tags, and notes.</p>
    
    <table class="hosts-table">
        <thead>
            <tr>
                <th>IP</th>
                <th>Hostname</th>
                <th>MAC</th>
                <th>Vendor</th>
                <th>Status</th>
                <th>Label</th>
                <th>Safe</th>
                <th>Tags</th>
                <th>Notes</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            % import time
            % for host in hosts:
            <tr class="status-{{host['last_status']}}">
                <td>{{host['ip']}}</td>
                <td>{{host['hostname'] or '-'}}</td>
                <td>{{host['mac'] or '-'}}</td>
                <td>{{host['vendor'] or '-'}}</td>
                <td><span class="status-badge status-{{host['last_status']}}">{{host['last_status']}}</span></td>
                <td>{{host.get('profile_label') or '-'}}</td>
                <td>
                    % if host.get('profile_is_safe'):
                    <span class="safe-badge">✓ Safe</span>
                    % else:
                    <span class="unsafe-badge">⚠ Unknown</span>
                    % end
                </td>
                <td>{{host.get('profile_tags') or '-'}}</td>
                <td>{{host.get('profile_notes') or '-'}}</td>
                <td>
                    <button onclick="editHost('{{host['ip']}}', '{{host.get('profile_label') or ''}}', {{1 if host.get('profile_is_safe') else 0}}, '{{host.get('profile_tags') or ''}}', '{{host.get('profile_notes') or ''}}')">Edit</button>
                </td>
            </tr>
            % end
            % if not hosts:
            <tr>
                <td colspan="10" class="no-results">No hosts found</td>
            </tr>
            % end
        </tbody>
    </table>
</div>

<!-- Edit Modal -->
<div id="editModal" class="modal" style="display: none;">
    <div class="modal-content">
        <span class="close" onclick="closeModal()">&times;</span>
        <h3>Edit Device</h3>
        <form method="POST" action="/admin/hosts/{{host_id}}/update" id="editForm">
            <input type="hidden" name="host_ip" id="host_ip">
            <div class="form-group">
                <label for="label">Label:</label>
                <input type="text" name="label" id="label" placeholder="Device name">
            </div>
            <div class="form-group">
                <label for="is_safe">
                    <input type="checkbox" name="is_safe" id="is_safe" value="true">
                    Mark as Safe
                </label>
            </div>
            <div class="form-group">
                <label for="tags">Tags (comma-separated):</label>
                <input type="text" name="tags" id="tags" placeholder="laptop, work, etc">
            </div>
            <div class="form-group">
                <label for="notes">Notes:</label>
                <textarea name="notes" id="notes" rows="3" placeholder="Additional notes"></textarea>
            </div>
            <div class="form-actions">
                <button type="submit">Save</button>
                <button type="button" onclick="closeModal()">Cancel</button>
            </div>
        </form>
    </div>
</div>

<script>
let currentHostIp = null;

function editHost(ip, label, isSafe, tags, notes) {
    currentHostIp = ip;
    document.getElementById('host_ip').value = ip;
    document.getElementById('label').value = label || '';
    document.getElementById('is_safe').checked = isSafe === 1;
    document.getElementById('tags').value = tags || '';
    document.getElementById('notes').value = notes || '';
    document.getElementById('editForm').action = '/admin/hosts/' + ip + '/update';
    document.getElementById('editModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('editModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    if (event.target == modal) {
        closeModal();
    }
}
</script>

<style>
.modal {
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgba(0,0,0,0.4);
}

.modal-content {
    background-color: #fefefe;
    margin: 15% auto;
    padding: 20px;
    border: 1px solid #888;
    width: 80%;
    max-width: 500px;
    border-radius: 8px;
}

.close {
    color: #aaa;
    float: right;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
}

.close:hover {
    color: #000;
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
}

.form-group input[type="text"],
.form-group textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

.form-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
}

.form-actions button {
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
}

.form-actions button[type="submit"] {
    background-color: #2c3e50;
    color: white;
}

.form-actions button[type="button"] {
    background-color: #ccc;
    color: #333;
}

.safe-badge {
    color: #155724;
    font-weight: 600;
}

.unsafe-badge {
    color: #721c24;
    font-weight: 600;
}
</style>

