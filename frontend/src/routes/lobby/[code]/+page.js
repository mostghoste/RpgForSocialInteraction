// frontend/src/routes/lobby/[code]/+page.js
import { redirect } from '@sveltejs/kit';

/**
 *  We do NOT want SvelteKit to pre‑render dynamic lobby pages at build time,
 *  so leave prerender disabled. The page is rendered client‑side after the
 *  room code is verified via the Django API.
 */
export const prerender = false;

/** @type {import('./$types').PageLoad} */
export async function load({ params, fetch }) {
	// Room code from the URL  ->  /lobby/ABCD
	const code = params.code;

	// This constant is injected at build time from the Docker ARG
	// VITE_API_BASE_URL="http://localhost:8000"
	// It remains a literal string inside the browser bundle.
	const base = import.meta.env.VITE_API_BASE_URL;

	// Ask the Django backend if the room exists / is still active
	const res = await fetch(
		`${base}/api/verify_room/?code=${encodeURIComponent(code)}`
	);

	// Room not found → kick user back to the landing page
	if (!res.ok) {
		throw redirect(303, '/');
	}

	const info = await res.json();

	// If the room is already completed (or some other invalid state) → redirect
	if (!['pending', 'in_progress', 'guessing'].includes(info.status)) {
		throw redirect(303, '/');
	}

	// Hand the data to +page.svelte as the `data` prop
	return {
		roomCode: code,
		lobbyState: info
	};
}
