import { redirect } from '@sveltejs/kit';

export async function load({ params, request, fetch, locals }) {
  const code = params.code;

  // Verify the room exists.
  const verifyRes = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/verify_room/?code=${encodeURIComponent(code)}`, { method: 'GET' });
  if (!verifyRes.ok) {
    throw redirect(303, '/');
  }
  const verifyData = await verifyRes.json();
  if (!['pending', 'in_progress', 'guessing'].includes(verifyData.status)) {
    throw redirect(303, '/');
  }

  // If authenticated, join automatically.
  if (locals.user) {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/join_room/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
    if (!res.ok) throw redirect(303, '/');
    const lobbyState = await res.json();
    return { lobbyState, needsUsername: false };
  }

  // For unauthenticated users:
  // If the room is pending, require a guest username.
  if (verifyData.status === 'pending') {
    return { roomCode: code, needsUsername: true };
  }
  // Otherwise (if the game is already underway) let the client try to rejoin.
  return { lobbyState: verifyData, needsUsername: false };
}