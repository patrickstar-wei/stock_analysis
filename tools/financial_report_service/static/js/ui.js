function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function fmtNum(v, unit) {
  if (v == null) return '—';
  if (unit === '%') return (v * (v < 10 ? 1 : 0.01)).toFixed(2) + '%';
  if (Math.abs(v) >= 1e12) return (v / 1e12).toFixed(2) + '万亿';
  if (Math.abs(v) >= 1e8) return (v / 1e8).toFixed(2) + '亿';
  if (Math.abs(v) >= 1e4) return (v / 1e4).toFixed(2) + '万';
  return v.toFixed(2);
}

function fmtDate(d) {
  if (!d) return '—';
  return d.replace('T', ' ').substring(0, 19);
}

function statusBadge(s) {
  const map = {
    succeeded: 'badge-green', failed: 'badge-red', running: 'badge-blue',
    queued: 'badge-gray', partial: 'badge-amber',
    downloaded: 'badge-green', skipped_exists: 'badge-blue',
    parsed: 'badge-green', parsed_no_metric: 'badge-amber',
    scanned_skipped: 'badge-amber', skipped_existing: 'badge-blue',
    pdf: 'badge-green', akshare: 'badge-blue', efinance: 'badge-purple', missing: 'badge-gray',
  };
  const labels = {
    succeeded: '成功', failed: '失败', running: '运行中', queued: '排队中', partial: '部分成功',
    downloaded: '已下载', skipped_exists: '缓存命中',
    parsed: '已解析', parsed_no_metric: '无指标', scanned_skipped: '扫描版',
    skipped_existing: '已存在', pdf: 'PDF', akshare: 'AkShare', efinance: 'efinance', missing: '缺失',
  };
  return `<span class="badge ${map[s] || 'badge-gray'}">${labels[s] || s}</span>`;
}

function exchangeLabel(e) {
  const map = { SZSE: '深交所', SSE: '上交所', BSE: '北交所' };
  return map[e] || e || '—';
}
