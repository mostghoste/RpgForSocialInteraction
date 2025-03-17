import { redirect } from '@sveltejs/kit';

export async function load({ params, request, fetch, locals }) {
  // If the user is authenticated, assume no guest username is needed.
  if (locals.user) {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/join_room/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // For authenticated users, no need to include guest_username
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
  
  // Unauthenticated users: Check if a guest_username cookie is present.
  const cookieHeader = request.headers.get('cookie') || '';
  const guestCookie = cookieHeader.split('; ').find(row => row.startsWith('guest_username='));
  const guestUsername = guestCookie ? decodeURIComponent(guestCookie.split('=')[1]) : null;
  
  if (guestUsername) {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/join_room/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: params.code, guest_username: guestUsername })
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
  
  // If no guest username is provided for an unauthenticated user,
  // signal that the page should show an input for guest username.
  return { roomCode: params.code, needsUsername: true };
}
