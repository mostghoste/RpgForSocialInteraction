import { redirect, error } from '@sveltejs/kit';

export async function load({ params, fetch }) {
  // Call the join_room endpoint to both validate the room and register the participant.
  const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/join_room/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: params.code })
  });
  
  // If the join fails (e.g., room doesn't exist or game is not joinable), redirect to home.
  if (!res.ok) {
    console.error("Join room failed", res.status);
    throw redirect(303, '/');
  }
  
  const lobbyState = await res.json();
  console.log("Loaded lobbyState:", lobbyState);
  
  // If the game status is not 'pending', redirect (i.e. game has started or finished).
  if (lobbyState.status !== 'pending') {
    throw redirect(303, '/');
  }
  
  return { lobbyState };
}
