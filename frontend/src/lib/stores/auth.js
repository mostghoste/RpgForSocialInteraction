// frontend/src/lib/stores/auth.js
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export const access = writable(null);
export const refresh = writable(null);

export function setTokens({ access: a, refresh: r }) {
  access.set(a);
  refresh.set(r);

  if (browser) {
    localStorage.setItem('access', a);
    localStorage.setItem('refresh', r);
  }
}

export function clearTokens() {
  access.set(null);
  refresh.set(null);

  if (browser) {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
  }
}

if (browser) {
  const a0 = localStorage.getItem('access');
  const r0 = localStorage.getItem('refresh');
  if (a0 && r0) {
    access.set(a0);
    refresh.set(r0);
  }
}
