function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  document.querySelector(`.nav-item[data-page="${page}"]`).classList.add('active');
  const titles = { dashboard: '仪表盘', query: '获取数据', data: '数据浏览', jobs: '任务列表' };
  document.getElementById('topbarTitle').textContent = titles[page] || '';
  if (page === 'dashboard') loadDashboard();
  if (page === 'data') loadCompanies();
  if (page === 'jobs') renderJobs();
}

loadDashboard();
