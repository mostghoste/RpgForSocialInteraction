import { get } from 'svelte/store';
import { access } from './stores/auth';

export async function apiFetch(path, opts = {}) {
  const token = get(access);
  const headers = {
    ...(opts.headers || {}),
    ...(token && { Authorization: `Bearer ${token}` })
  };
  const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}${path}`, {
    ...opts,
    headers
  });
  // optionally handle 401 → refresh flow here
  return res;
}
