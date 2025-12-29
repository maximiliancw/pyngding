<article>
    <header>
        <h2>Recent Scan Runs</h2>
    </header>
    <table>
        <thead>
            <tr>
                <th>Time</th>
                <th>Targets</th>
                <th>Up</th>
                <th>Down</th>
            </tr>
        </thead>
        <tbody>
            % if runs:
            % import time
            % for run in runs[:10]:
            <tr>
                <td>{{!time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(run['finished_ts']))}}</td>
                <td>{{run['targets_count']}}</td>
                <td>{{run['up_count']}}</td>
                <td>{{run['down_count']}}</td>
            </tr>
            % end
            % else:
            <tr>
                <td colspan="4" style="text-align: center; padding: 2rem; color: var(--pico-muted-color);">No scan runs yet</td>
            </tr>
            % end
        </tbody>
    </table>
</article>

