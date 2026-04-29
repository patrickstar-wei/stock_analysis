async function loadDashboard() {
  const stats = await api('/dashboard/stats');
  document.getElementById('dashStats').innerHTML = [
    { label: '公司数', value: stats.company_count, cls: 'accent' },
    { label: '报告数', value: stats.report_count, cls: 'blue' },
    { label: '指标数', value: stats.metric_count, cls: 'amber' },
    { label: '缓存命中', value: stats.cached_count, cls: '' },
  ].map(s => `<div class="stat-card"><div class="label">${s.label}</div><div class="value ${s.cls}">${s.value}</div></div>`).join('');

  const companies = await api('/companies');
  document.getElementById('dashCompanies').innerHTML = companies.slice(0, 20).map(c => `
    <tr class="clickable" onclick="viewCompany('${c.code}')">
      <td class="mono">${c.code}</td>
      <td>${c.name || '—'}</td>
      <td>${exchangeLabel(c.exchange)}</td>
      <td class="mono">${c.period_count}</td>
      <td class="mono">${c.metric_count}</td>
      <td class="mono" style="font-size:11px;">${fmtDate(c.updated_at)}</td>
    </tr>`).join('');

  document.getElementById('sidebarStats').innerHTML = `
    <div class="stat-row"><span>公司</span><span class="stat-val">${stats.company_count}</span></div>
    <div class="stat-row"><span>报告</span><span class="stat-val">${stats.report_count}</span></div>
    <div class="stat-row"><span>指标</span><span class="stat-val">${stats.metric_count}</span></div>`;
}
