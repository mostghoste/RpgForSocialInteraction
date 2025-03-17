import { redirect } from '@sveltejs/kit';

export async function load({ params, request, fetch, locals }) {
  const code = params.code;

  // Verify that the room exists and is joinable.
  const verifyRes = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/verify_room/?code=${encodeURIComponent(code)}`, {
    method: 'GET'
  });
  if (!verifyRes.ok) {
    console.error("Room verification failed", verifyRes.status);
    throw redirect(303, '/');
  }
  const verifyData = await verifyRes.json();
  if (verifyData.status !== 'pending') {
    throw redirect(303, '/');
  }

  // If user is authenticated, join automatically.
  if (locals.user) {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/join_room/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
    if (!res.ok) {
      console.error("Join room failed", res.status);
      throw redirect(303, '/');
    }
    const lobbyState = await res.json();
    return { lobbyState, needsUsername: false };
  }

  // For unauthenticated users, don't call join_room yet.
  // Instead, signal that a guest username is required.
  return { roomCode: code, needsUsername: true };
}
