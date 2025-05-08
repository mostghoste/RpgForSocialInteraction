// frontend/src/lib/stores/auth.js
import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';

export const access = writable(null);
export const refresh = writable(null);
export const user = writable(null);

export function setTokens({ access: a, refresh: r }) {
  access.set(a);
  if (browser) localStorage.setItem('access', a);

  if (r) {
    refresh.set(r);
    if (browser) localStorage.setItem('refresh', r);
  }

  loadUser();
}

export function clearTokens() {
  access.set(null);
  refresh.set(null);
  user.set(null);
  if (browser) {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
  }
}

async function loadUser() {
  const token = get(access);
  if (!token) {
    return;
  }

  const { apiFetch } = await import('$lib/api');

  try {
    const res = await apiFetch('/api/user/');
    if (res.ok) {
      const data = await res.json();
      user.set(data);
    } else if (res.status === 401) {
      clearTokens();
    }
  } catch (err) {
    clearTokens();
  }
}

if (browser) {
  const a0 = localStorage.getItem('access');
  const r0 = localStorage.getItem('refresh');
  if (a0 && r0) {
    access.set(a0);
    refresh.set(r0);
    loadUser();
  }
}
