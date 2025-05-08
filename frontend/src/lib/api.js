// frontend/src/lib/api.js
import { get } from 'svelte/store';
import { access, refresh } from '$lib/stores/auth';

const API_URL = import.meta.env.VITE_API_BASE_URL;

export async function apiFetch(path, opts = {}) {
  const token = get(access);
  const headers = {
    ...(opts.headers || {}),
    ...(token && { Authorization: `Bearer ${token}` })
  };

  let res = await fetch(`${API_URL}${path}`, { ...opts, headers });

  if (res.status === 401 && get(refresh)) {
    const { setTokens, clearTokens } = await import('$lib/stores/auth');

    const refreshRes = await fetch(`${API_URL}/api/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: get(refresh) })
    });

    if (refreshRes.ok) {
      const data = await refreshRes.json();
      setTokens(data);

      const newToken = data.access;
      const retryHeaders = {
        ...(opts.headers || {}),
        Authorization: `Bearer ${newToken}`
      };
      res = await fetch(`${API_URL}${path}`, { ...opts, headers: retryHeaders });
    } else {
      clearTokens();
      throw new Error('Session expired');
    }
  }

  return res;
}
