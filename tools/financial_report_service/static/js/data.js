let currentCompany = null;
let currentPeriod = null;

async function loadCompanies() {
  const companies = await api('/companies');
  renderCompanyTable(companies);
}

async function searchCompanies(q) {
  if (!q.trim()) { loadCompanies(); return; }
  const companies = await api('/companies/search?q=' + encodeURIComponent(q));
  renderCompanyTable(companies);
}

function renderCompanyTable(companies) {
  document.getElementById('companyList').innerHTML = companies.length === 0
    ? '<tr><td colspan="6" style="text-align:center;color:var(--text-2);padding:30px;">暂无数据</td></tr>'
    : companies.map(c => `
    <tr class="clickable" onclick="viewCompany('${c.code}')">
      <td class="mono">${c.code}</td>
      <td>${c.name || '—'}</td>
      <td>${exchangeLabel(c.exchange)}</td>
      <td class="mono">${c.period_count}</td>
      <td class="mono">${c.metric_count}</td>
      <td class="mono" style="font-size:11px;">${fmtDate(c.updated_at)}</td>
    </tr>`).join('');
}

async function viewCompany(code) {
  currentCompany = code;
  document.getElementById('dataListView').style.display = 'none';
  document.getElementById('dataDetailView').style.display = '';
  navigate('data');

  const [metrics, reports] = await Promise.all([
    api('/companies/' + code + '/metrics'),
    api('/companies/' + code + '/reports'),
  ]);

  const periods = [...new Set(metrics.map(m => m.report_period))].sort().reverse();
  currentPeriod = periods[0] || null;

  const company = reports.length > 0 ? reports[0] : { name: code, exchange: '' };
  document.getElementById('detailHeader').innerHTML = `
    <span class="code">${code}</span>
    <span class="name">${company.name || '—'}</span>
    <span class="exchange">${exchangeLabel(company.exchange)}</span>`;

  document.getElementById('periodTabs').innerHTML = periods.map(p => `
    <div class="period-tab ${p === currentPeriod ? 'active' : ''}" onclick="selectPeriod('${p}')">${p}</div>`).join('');

  renderPeriodMetrics(metrics, currentPeriod);

  document.getElementById('detailReports').innerHTML = reports.map(r => `
    <tr>
      <td style="font-size:12px;">${r.title || '—'}</td>
      <td>${r.report_type || '—'}</td>
      <td class="mono">${r.report_period || '—'}</td>
      <td>${statusBadge(r.fetch_status)}</td>
      <td>${statusBadge(r.parse_status)}</td>
    </tr>`).join('');
}

function selectPeriod(period) {
  currentPeriod = period;
  document.querySelectorAll('.period-tab').forEach(t => t.classList.toggle('active', t.textContent === period));
  api('/companies/' + currentCompany + '/metrics').then(metrics => renderPeriodMetrics(metrics, period));
}

function renderPeriodMetrics(allMetrics, period) {
  const filtered = allMetrics.filter(m => m.report_period === period);
  document.getElementById('detailMetrics').innerHTML = filtered.length === 0
    ? '<div class="empty-state"><div class="desc">该报告期暂无指标数据</div></div>'
    : '<div class="metric-grid">' + filtered.map(m => `
      <div class="metric-item">
        <div class="m-name">${m.metric_name}</div>
        <div class="m-value">${fmtNum(m.metric_value, m.unit)}</div>
        <div class="m-meta">
          ${statusBadge(m.source)}
          <span class="mono" style="font-size:10px;">${(m.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>`).join('') + '</div>';
}

function showCompanyList() {
  document.getElementById('dataListView').style.display = '';
  document.getElementById('dataDetailView').style.display = 'none';
  currentCompany = null;
}
