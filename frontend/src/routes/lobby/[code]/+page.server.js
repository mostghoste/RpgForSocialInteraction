// frontend/src/routes/lobby/[code]/+page.server.js
import { redirect } from '@sveltejs/kit';

export async function load({ params, fetch }) {
  const code = params.code;
  const base = import.meta.env.VITE_API_BASE_URL;

  const verify = await fetch(
    `${base}/api/verify_room/?code=${encodeURIComponent(code)}`
  );
  if (!verify.ok) {
    throw redirect(303, '/');
  }
  const info = await verify.json();

  if (!['pending', 'in_progress', 'guessing'].includes(info.status)) {
    throw redirect(303, '/');
  }

  return {
    roomCode: code,
    lobbyState: info
  };
}
