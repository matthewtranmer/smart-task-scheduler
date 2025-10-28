const fmtNum = (n) => new Intl.NumberFormat().format(n);

async function fetchJSON(url) {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}

function buildSpark(el, data) {
    new Chart(el.getContext('2d'), {
    type: 'line',
    data: { labels: data.labels, datasets: [{ data: data.values, fill: false, tension: 0.3 }] },
    options: {
        responsive: true,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        elements: { point: { radius: 0 } },
        scales: { x: { display: false }, y: { display: false } }
    }
    });
}

async function loadDashboard() {
    const [metrics, cats, table] = await Promise.all([
    fetchJSON('/api/metrics?days=30'),
    fetchJSON('/api/categories'),
    fetchJSON('/api/table?limit=100')
    ]);

    // KPIs
    document.getElementById('kpi-total').textContent = fmtNum(metrics.total);
    document.getElementById('kpi-avg').textContent = fmtNum(metrics.avg_duration_ms);
    document.getElementById('kpi-success').textContent = metrics.success_rate + '%';
    document.getElementById('kpi-active').textContent = fmtNum(metrics.active_now);

    buildSpark(document.getElementById('spark1'), metrics.spark);
    buildSpark(document.getElementById('spark2'), metrics.spark);
    buildSpark(document.getElementById('spark3'), metrics.spark);
    buildSpark(document.getElementById('spark4'), metrics.spark);

    // Line chart
    new Chart(document.getElementById('chart-line').getContext('2d'), {
    type: 'line',
    data: { labels: metrics.series.labels, datasets: [{ label: 'Jobs', data: metrics.series.values, fill: true, tension: 0.3 }] },
    options: { plugins: { legend: { display: false } } }
    });

    // Bar chart
    new Chart(document.getElementById('chart-bar').getContext('2d'), {
    type: 'bar',
    data: { labels: cats.map(c => c.label), datasets: [{ label: 'Share %', data: cats.map(c => c.pct) }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100 } } }
    });

    // Table
    const tbody = document.querySelector('#jobs tbody');
    const rows = table.rows;
    tbody.innerHTML = rows.map(r => `
    <tr>
        <td><code>${r.id}</code></td>
        <td>${r.owner}</td>
        <td>
        <span class="badge text-bg-${{
            'Queued':'secondary','Running':'info','Succeeded':'success','Failed':'danger'
        }[r.status]}">${r.status}</span>
        </td>
        <td class="text-end">${fmtNum(r.duration_ms)}</td>
        <td><time datetime="${r.created_at}">${r.created_at}</time></td>
    </tr>`).join('');

    // simple client-side filter
    const q = document.getElementById('q');
    q.addEventListener('input', () => {
    const needle = q.value.toLowerCase();
    for (const tr of tbody.querySelectorAll('tr')) {
        tr.style.display = tr.textContent.toLowerCase().includes(needle) ? '' : 'none';
    }
    });
}

document.getElementById('refresh').addEventListener('click', () => loadDashboard());
loadDashboard().catch(err => console.error(err));
