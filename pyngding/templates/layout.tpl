<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title or 'pyngding'}}</title>
    <link rel="stylesheet" href="/static/styles.css">
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <h1 class="nav-title">pyngding</h1>
            <div class="nav-links">
                <a href="/">Dashboard</a>
                <a href="/hosts">Hosts</a>
                % if auth_enabled:
                <a href="/admin/settings">Settings</a>
                <a href="/admin/api-keys">API Keys</a>
                <a href="/admin/hosts">Device Inventory</a>
                % end
            </div>
        </div>
    </nav>
    <main class="container">
        {{!base}}
    </main>
</body>
</html>

