// frontend/src/lib/stores/auth.js
import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';
import { apiFetch } from '$lib/api';

export const access = writable(null);
export const refresh = writable(null);
export const user = writable(null);

export function setTokens({ access: a, refresh: r }) {
  access.set(a);
  refresh.set(r);

  if (browser) {
    localStorage.setItem('access', a);
    localStorage.setItem('refresh', r);
  }

  loadUser();
}

export function clearTokens() {
  access.set(null);
  refresh.set(null);

  if (browser) {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
  }

  user.set(null);
}

async function loadUser() {
    const token = get(access);
    if (!token) return;
    try {
      const res = await apiFetch('/api/user/');
      if (res.ok) {
        user.set(await res.json());
      } else {
        clearTokens();
      }
    } catch {
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
