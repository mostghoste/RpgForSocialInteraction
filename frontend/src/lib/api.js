import { get } from 'svelte/store';
import { access, refresh, setTokens, clearTokens } from './stores/auth';

const API_URL = import.meta.env.VITE_API_BASE_URL;

export async function apiFetch(path, opts = {}) {
  // Prepare headers with current access token
  let token = get(access);
  const headers = {
    ...(opts.headers || {}),
    ...(token && { Authorization: `Bearer ${token}` })
  };

  // First attempt
  let res = await fetch(`${API_URL}${path}`, { ...opts, headers });

  // If expired, try refreshing
  if (res.status === 401 && get(refresh)) {
    const refreshRes = await fetch(`${API_URL}/api/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: get(refresh) })
    });

    if (refreshRes.ok) {
      const data = await refreshRes.json();
      // update both tokens in your store
      setTokens(data);
      token = data.access;

      // retry original request once with new token
      const retryHeaders = {
        ...(opts.headers || {}),
        Authorization: `Bearer ${token}`
      };
      res = await fetch(`${API_URL}${path}`, { ...opts, headers: retryHeaders });
    } else {
      // refresh also failed, force logout
      clearTokens();
      throw new Error('Sesija pasibaigė. Prašome prisijungti iš naujo.');
    }
  }

  return res;
}
