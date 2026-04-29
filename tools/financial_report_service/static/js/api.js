const API = '/api/v1';

async function api(path, opts = {}) {
  try {
    const res = await fetch(API + path, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    return await res.json();
  } catch (e) {
    toast(e.message, 'error');
    throw e;
  }
}
