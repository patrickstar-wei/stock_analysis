let stockCodes = [];

function handleCodeInput(e) {
  if (e.key === 'Enter') {
    e.preventDefault();
    const val = e.target.value.trim();
    if (/^\d{6}$/.test(val) && !stockCodes.includes(val)) {
      stockCodes.push(val);
      renderCodeTags();
    } else if (stockCodes.includes(val)) {
      toast('代码已存在', 'info');
    } else {
      toast('请输入6位数字股票代码', 'error');
    }
    e.target.value = '';
  }
}

function renderCodeTags() {
  const area = document.getElementById('codeInputArea');
  const input = document.getElementById('codeInput');
  area.querySelectorAll('.tag').forEach(t => t.remove());
  stockCodes.forEach((code, i) => {
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.innerHTML = `${code}<span class="remove" onclick="removeCode(${i})">×</span>`;
    area.insertBefore(tag, input);
  });
}

function removeCode(i) {
  stockCodes.splice(i, 1);
  renderCodeTags();
}

function toggleReportType(btn) {
  btn.classList.toggle('active');
  if (btn.classList.contains('active')) {
    btn.textContent = '✓ ' + btn.textContent.replace('✓ ', '');
  } else {
    btn.textContent = btn.textContent.replace('✓ ', '');
  }
}

async function submitJob() {
  if (stockCodes.length === 0) { toast('请至少添加一个股票代码', 'error'); return; }
  const types = Array.from(document.querySelectorAll('.report-type-btn.active')).map(b => b.dataset.value);
  if (types.length === 0) { toast('请选择至少一种报告类型', 'error'); return; }

  const csvContent = 'code\n' + stockCodes.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const form = new FormData();
  form.append('file', blob, 'codes.csv');
  form.append('years', document.getElementById('years').value);
  form.append('report_types', types.join(','));
  form.append('full_refresh', document.getElementById('fullRefresh').checked ? 'true' : 'false');

  try {
    const res = await fetch(API + '/jobs', { method: 'POST', body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    toast('任务已提交: ' + data.job_id.substring(0, 8), 'success');
    jobs[data.job_id] = { status: data.status, created_at: data.created_at };
    stockCodes = [];
    renderCodeTags();
    pollJob(data.job_id);
  } catch (e) {
    toast(e.message, 'error');
  }
}
