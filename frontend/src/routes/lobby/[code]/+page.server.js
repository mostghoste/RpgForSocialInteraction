import { redirect } from '@sveltejs/kit';

export async function load({ params, fetch, locals }) {
  const code = params.code;
  const base = import.meta.env.VITE_API_BASE_URL;

  // verify exists
  const verify = await fetch(`${base}/api/verify_room/?code=${encodeURIComponent(code)}`);
  if (!verify.ok) throw redirect(303, '/');
  const info = await verify.json();
  if (!['pending','in_progress','guessing'].includes(info.status)) {
    throw redirect(303, '/');
  }

  // if logged in, auto‐join
  if (locals.user) {
    const join = await fetch(`${base}/api/join_room/`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ code })
    });
    if (!join.ok) throw redirect(303, '/');
    const lobbyState = await join.json();
    return { lobbyState, needsUsername: false };
  }

  // unauthenticated: if room is pending, ask for guest name
  if (info.status === 'pending') {
    return { roomCode: code, needsUsername: true };
  }

  // otherwise let client restore
  return { lobbyState: info, needsUsername: false };
}
