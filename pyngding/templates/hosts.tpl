% rebase('layout.tpl', title='Hosts')
<div class="hosts-page">
    <h2>Hosts</h2>
    
    <div class="filters">
        <form method="get" action="/hosts" hx-get="/partials/hosts-table" hx-target="#hosts-table" hx-trigger="submit, input delay:500ms from:input">
            <input type="text" name="search" placeholder="Search IP, hostname, MAC, vendor..." value="{{search}}" 
                   hx-get="/partials/hosts-table" hx-target="#hosts-table" hx-trigger="input delay:500ms">
            <select name="status" 
                    hx-get="/partials/hosts-table" hx-target="#hosts-table" hx-trigger="change">
                <option value="">All Status</option>
                <option value="up" {{'selected' if status_filter == 'up' else ''}}>Up</option>
                <option value="down" {{'selected' if status_filter == 'down' else ''}}>Down</option>
            </select>
        </form>
    </div>
    
    <div id="hosts-table" hx-get="/partials/hosts-table?status={{status_filter}}&search={{search}}" hx-trigger="every 10s" hx-swap="innerHTML">
        % include('partials/hosts-table.tpl', hosts=hosts)
    </div>
</div>

