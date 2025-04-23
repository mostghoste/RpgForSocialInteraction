import { writable } from 'svelte/store';

export const access = writable(null);
export const refresh = writable(null);

export function setTokens({ access: a, refresh: r }) {
  access.set(a);
  refresh.set(r);
  localStorage.setItem('access', a);
  localStorage.setItem('refresh', r);
}

export function clearTokens() {
  access.set(null);
  refresh.set(null);
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
}

// on app init, load from localStorage
const a0 = localStorage.getItem('access');
const r0 = localStorage.getItem('refresh');
if (a0 && r0) setTokens({ access: a0, refresh: r0 });
