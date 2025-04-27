// frontend/src/routes/lobby/[code]/+page.server.js
import { redirect } from '@sveltejs/kit';

export async function load({ params, fetch }) {
  const code = params.code;
  const base = import.meta.env.VITE_API_BASE_URL;

  // 1) Verify the room exists and get its public state
  const verify = await fetch(
    `${base}/api/verify_room/?code=${encodeURIComponent(code)}`
  );
  if (!verify.ok) {
    // Room doesn't exist (or other error) → send back to home
    throw redirect(303, '/');
  }
  const info = await verify.json();

  // 2) Only allow rooms that are still joinable
  if (!['pending', 'in_progress', 'guessing'].includes(info.status)) {
    throw redirect(303, '/');
  }

  // 3) Tell the client whether we need to prompt for a guest name.
  //    The client will skip it automatically if `$user` is set.
  return {
    roomCode: code,
    lobbyState: info
  };
}
