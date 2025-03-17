import { redirect } from '@sveltejs/kit';

export async function load({ params, request, fetch, locals }) {
  // If the user is authenticated, join the room without a guest username.
  if (locals.user) {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/join_room/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: params.code })
    });
  
    if (!res.ok) {
      console.error("Join room failed", res.status);
      throw redirect(303, '/');
    }
  
    const lobbyState = await res.json();
  
    if (lobbyState.status !== 'pending') {
      throw redirect(303, '/');
    }
  
    return { lobbyState, needsUsername: false };
  }
  
  // For unauthenticated users, always require a guest username.
  return { roomCode: params.code, needsUsername: true };
}
