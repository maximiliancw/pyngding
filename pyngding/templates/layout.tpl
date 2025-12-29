<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title or 'pyngding'}}</title>
    <link rel="stylesheet" href="/static/pico.min.css">
    <link rel="stylesheet" href="/static/styles.css">
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <header>
        <nav class="container-fluid">
            <ul>
                <li><strong>pyngding</strong></li>
            </ul>
            <ul>
                <li><a href="/">Dashboard</a></li>
                <li><a href="/hosts">Hosts</a></li>
                % if auth_enabled:
                <li><a href="/admin/settings">Settings</a></li>
                <li><a href="/admin/api-keys">API Keys</a></li>
                <li><a href="/admin/hosts">Device Inventory</a></li>
                <li><a href="/admin/adguard">AdGuard</a></li>
                <li><a href="/admin/ipv6">IPv6</a></li>
                % end
            </ul>
        </nav>
    </header>
    <main class="container">
        {{!base}}
    </main>
</body>
</html>

