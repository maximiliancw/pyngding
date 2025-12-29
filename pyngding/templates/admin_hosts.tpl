% rebase('layout.tpl', title='Device Inventory', auth_enabled=auth_enabled)
<article>
    <header>
        <h1>Device Inventory</h1>
        <p>Manage device labels, safety flags, tags, and notes.</p>
    </header>
    
    <table>
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
            <tr>
                <td>{{host['ip']}}</td>
                <td>{{host['hostname'] or '-'}}</td>
                <td>{{host['mac'] or '-'}}</td>
                <td>{{host['vendor'] or '-'}}</td>
                <td>
                    % if host['last_status'] == 'up':
                    <mark style="background-color: var(--pico-ins-color); color: var(--pico-background-color); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{{host['last_status']}}</mark>
                    % else:
                    <mark style="background-color: var(--pico-del-color); color: var(--pico-background-color); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">{{host['last_status']}}</mark>
                    % end
                </td>
                <td>{{host.get('profile_label') or '-'}}</td>
                <td>
                    % if host.get('profile_is_safe'):
                    <mark style="background-color: var(--pico-ins-color); color: var(--pico-background-color); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">✓ Safe</mark>
                    % else:
                    <mark style="background-color: var(--pico-del-color); color: var(--pico-background-color); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">⚠ Unknown</mark>
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
                <td colspan="10" style="text-align: center; padding: 2rem; color: var(--pico-muted-color);">No hosts found</td>
            </tr>
            % end
        </tbody>
    </table>
</article>

<!-- Edit Modal -->
<dialog id="editModal">
    <article>
        <header>
            <h3>Edit Device</h3>
            <button aria-label="Close" rel="prev" onclick="closeModal()"></button>
        </header>
        <form method="POST" action="/admin/hosts/{{host_id}}/update" id="editForm">
            <input type="hidden" name="host_ip" id="host_ip">
            <label for="label">Label:</label>
            <input type="text" name="label" id="label" placeholder="Device name">
            <label for="is_safe">
                <input type="checkbox" name="is_safe" id="is_safe" value="true">
                Mark as Safe
            </label>
            <label for="tags">Tags (comma-separated):</label>
            <input type="text" name="tags" id="tags" placeholder="laptop, work, etc">
            <label for="notes">Notes:</label>
            <textarea name="notes" id="notes" rows="3" placeholder="Additional notes"></textarea>
            <footer>
                <button type="submit">Save</button>
                <button type="button" class="secondary" onclick="closeModal()">Cancel</button>
            </footer>
        </form>
    </article>
</dialog>

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
    document.getElementById('editModal').showModal();
}

function closeModal() {
    document.getElementById('editModal').close();
}
</script>

