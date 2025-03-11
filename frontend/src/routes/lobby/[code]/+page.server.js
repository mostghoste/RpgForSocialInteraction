// lobby/[code]/+page.server.js

import { redirect, error } from '@sveltejs/kit';

export async function load({ params, fetch }) {
  // Call an endpoint to get the lobby state without modifying it.
  const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/lobby_state/?code=${params.code}`);
  
  if (!res.ok) {
    // If the lobby doesn't exist or another error, redirect or show error.
    throw redirect(303, '/');
  }
  
  const lobbyState = await res.json();
  
  // If game already started (adjust condition based on your logic)
  if (lobbyState.status !== 'pending') {
    throw redirect(303, '/');
  }
  
  return { lobbyState };
}