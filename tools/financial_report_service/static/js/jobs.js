let jobs = {};

async function pollJob(jobId) {
  const poll = async () => {
    const s = await api('/jobs/' + jobId);
    jobs[jobId] = s;
    renderJobs();
    if (s.status === 'running' || s.status === 'queued') {
      setTimeout(poll, 2000);
    } else {
      toast(`任务 ${jobId.substring(0, 8)} ${s.status === 'succeeded' ? '完成' : s.status === 'partial' ? '部分完成' : '失败'}`,
            s.status === 'succeeded' ? 'success' : s.status === 'partial' ? 'info' : 'error');
      loadDashboard();
    }
  };
  setTimeout(poll, 1000);
}

function renderJobs() {
  const list = Object.entries(jobs);
  const el = document.getElementById('jobList');
  const empty = document.getElementById('jobEmpty');
  if (list.length === 0) { el.innerHTML = ''; empty.style.display = ''; return; }
  empty.style.display = 'none';
  el.innerHTML = list.reverse().map(([id, j]) => `
    <div class="job-card">
      <div class="job-header">
        <span class="job-id">${id}</span>
        ${statusBadge(j.status)}
      </div>
      <div class="progress-bar"><div class="fill" style="width:${Math.round(j.progress * 100)}%"></div></div>
      <div class="job-info">
        <span>进度 ${j.done_codes || 0}/${j.total_codes || 0}</span>
        <span>成功 ${j.success_reports || 0}</span>
        <span>失败 ${j.failed_reports || 0}</span>
        ${j.cached_reports ? `<span>缓存 ${j.cached_reports}</span>` : ''}
      </div>
    </div>`).join('');
}
