<script>
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	const API_URL = import.meta.env.VITE_API_BASE_URL;

	// Data coming from the server load function.
	// It will either have { lobbyState, needsUsername: false } (for authed users)
	// or { roomCode, needsUsername: true } (for unauthenticated users).
	export let data;
	let needsUsername = data.needsUsername;
	let code = needsUsername ? data.roomCode : data.lobbyState.code;
	let lobbyState = needsUsername ? {} : data.lobbyState;
	let players = needsUsername ? [] : lobbyState.players || [];
	let errorMessage = '';

	// For storing the participant id and secret (if available)
	let participantId = lobbyState?.participant_id;
	let participantSecret = lobbyState?.secret;
	if (browser) {
		if (participantId) {
			localStorage.setItem('participantId', participantId);
		} else {
			participantId = localStorage.getItem('participantId');
		}
		if (participantSecret) {
			localStorage.setItem('participantSecret', participantSecret);
		} else {
			participantSecret = localStorage.getItem('participantSecret');
		}
	}

	// Variable for guest username input (for unauthenticated users)
	let guestUsername = '';

	let socket;
	let heartbeatInterval;

	// Host-specific state; these values are returned from the backend.
	let isHost = lobbyState?.is_host || false;
	let roundLength = lobbyState?.round_length || 60;
	let roundCount = lobbyState?.round_count || 3;

	// Connect the WebSocket to the lobby.
	function connectWebSocket() {
		let baseUrl = API_URL || 'http://localhost:8000';
		if (baseUrl.startsWith('https://')) {
			baseUrl = baseUrl.replace('https://', 'wss://');
		} else if (baseUrl.startsWith('http://')) {
			baseUrl = baseUrl.replace('http://', 'ws://');
		}
		const wsUrl = `${baseUrl}/ws/lobby/${code}/`;
		socket = new WebSocket(wsUrl);

		socket.onopen = () => {
			console.log(`Connected to lobby: ${code}`);
			heartbeatInterval = setInterval(() => {
				if (socket.readyState === WebSocket.OPEN) {
					socket.send(
						JSON.stringify({
							type: 'ping',
							participant_id: participantId
						})
					);
				}
			}, 15000);
		};

		socket.onerror = (event) => {
			console.error('WebSocket error:', event);
			errorMessage = 'Nepavyko prisijungti prie WS.';
		};

		socket.onmessage = (event) => {
			const data = JSON.parse(event.data);
			// Update players list when a lobby update is received.
			if (data.players) {
				players = data.players;
			}
			// Update settings if they change.
			if (data.round_length && data.round_count) {
				roundLength = data.round_length;
				roundCount = data.round_count;
			}
		};
	}

	// Function to join the room using a guest username.
	async function submitGuestUsername() {
		if (!guestUsername) {
			errorMessage = 'Prašome įvesti vartotojo vardą.';
			return;
		}
		errorMessage = '';
		try {
			const res = await fetch(`${API_URL}/api/join_room/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, guest_username: guestUsername })
			});
			if (!res.ok) {
				const data = await res.json().catch(() => ({}));
				errorMessage = data.error ?? 'Nepavyko prisijungti.';
				return;
			}
			const data = await res.json();
			// Update local state with the returned lobby state.
			lobbyState = data;
			players = lobbyState.players || [];
			participantId = lobbyState.participant_id;
			participantSecret = lobbyState.secret;
			if (browser && participantId) {
				localStorage.setItem('participantId', participantId);
				localStorage.setItem('participantSecret', participantSecret);
			}
			// Update host flag and settings.
			isHost = lobbyState.is_host || false;
			roundLength = lobbyState.round_length || 60;
			roundCount = lobbyState.round_count || 3;
			needsUsername = false;
			connectWebSocket();
		} catch (err) {
			console.error(err);
			errorMessage = 'Serverio klaida bandant prisijungti prie kambario.';
		}
	}

	// Function to leave the lobby.
	function leaveLobby() {
		if (socket) {
			socket.close();
		}
		goto('/');
	}

	// Host-only: Update session settings.
	async function updateSettings() {
		try {
			const secret = localStorage.getItem('participantSecret');
			const res = await fetch(`${API_URL}/api/update_settings/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret,
					round_length: roundLength,
					round_count: roundCount
				})
			});
			if (!res.ok) {
				const data = await res.json();
				errorMessage = data.error || 'Nepavyko atnaujinti nustatymų.';
				return;
			}
			const updated = await res.json();
			roundLength = updated.round_length;
			roundCount = updated.round_count;
		} catch (err) {
			console.error(err);
			errorMessage = 'Serverio klaida atnaujinant nustatymus.';
		}
	}

	// Host-only: Start the game.
	async function startGame() {
		try {
			const res = await fetch(`${API_URL}/api/start_game/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, participant_id: participantId })
			});
			if (!res.ok) {
				const data = await res.json();
				errorMessage = data.error || 'Nepavyko pradėti žaidimo.';
				return;
			}
			// Navigate to the game view (ensure you implement this route/endpoint).
			goto(`/game/${code}`);
		} catch (err) {
			console.error(err);
			errorMessage = 'Serverio klaida pradedant žaidimą.';
		}
	}

	onMount(() => {
		if (!needsUsername) {
			connectWebSocket();
		}
	});

	onDestroy(() => {
		if (heartbeatInterval) clearInterval(heartbeatInterval);
		if (socket) socket.close();
	});
</script>

{#if needsUsername}
	<!-- Guest user: Show username input form -->
	<h2>Kambario kodas: {code}</h2>
	<p>Prašome įvesti vartotojo vardą, kad prisijungtumėte prie kambario.</p>
	<input class="border" type="text" bind:value={guestUsername} placeholder="Vartotojo vardas" />
	<button class="border" on:click={submitGuestUsername}>Prisijungti</button>
	{#if errorMessage}
		<p class="error">{errorMessage}</p>
	{/if}
{:else}
	<!-- Lobby view -->
	<h2>Kambario kodas: {code}</h2>
	<p>Žaidėjai kambaryje:</p>
	<ul>
		{#each players as p}
			<li>{p}</li>
		{/each}
	</ul>
	{#if isHost}
		<!-- Host-only settings controls -->
		<div class="host-settings">
			<h3>Nustatymai (Tik vedėjui)</h3>
			<label>
				Round Length (s):
				<input type="number" bind:value={roundLength} min="1" />
			</label>
			<label>
				Round Count:
				<input type="number" bind:value={roundCount} min="1" />
			</label>
			<button class="border" on:click={updateSettings}>Atnaujinti nustatymus</button>
			<button class="border" on:click={startGame}>Pradėti žaidimą</button>
		</div>
	{/if}
	<button class="border" on:click={leaveLobby}>Palikti kambarį</button>
	{#if errorMessage}
		<p class="error">{errorMessage}</p>
	{/if}
{/if}
