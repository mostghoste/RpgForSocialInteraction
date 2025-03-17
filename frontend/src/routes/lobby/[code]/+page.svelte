<script>
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	const API_URL = import.meta.env.VITE_API_BASE_URL;

	// Data coming from the server load function.
	// It will either have { lobbyState, needsUsername: false } or { roomCode, needsUsername: true }
	export let data;
	let needsUsername = data.needsUsername;
	let code = needsUsername ? data.roomCode : data.lobbyState.code;
	let lobbyState = needsUsername ? {} : data.lobbyState;
	let players = needsUsername ? [] : lobbyState.players || [];
	let errorMessage = '';

	// For storing the participant id (if available)
	let participantId = lobbyState?.participant_id;
	if (participantId) {
		localStorage.setItem('participantId', participantId);
	} else {
		participantId = localStorage.getItem('participantId');
	}

	// Variables for guest username input
	let guestUsername = '';

	let socket;
	let heartbeatInterval;

	// Function to connect the websocket to the lobby.
	function connectWebSocket() {
		let baseUrl = API_URL || 'http://localhost:8000';
		// Convert http(s) to ws(s)
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
			// Expect updated lobby state including players
			if (data.players) {
				players = data.players;
			}
		};
	}

	// Function to join the room using the guest username.
	async function submitGuestUsername() {
		if (!guestUsername) {
			errorMessage = 'Prašome įvesti vartotojo vardą.';
			return;
		}
		errorMessage = '';
		// Optionally, store the username in a cookie so subsequent requests include it.
		document.cookie = `guest_username=${encodeURIComponent(guestUsername)}; path=/`;
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
			// Save the updated lobby state and participant id.
			lobbyState = data;
			players = lobbyState.players || [];
			participantId = lobbyState.participant_id;
			if (participantId) {
				localStorage.setItem('participantId', participantId);
			}
			// Now that the user has provided a username, hide the username form.
			needsUsername = false;
			// Establish the websocket connection.
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

	// If the user is already joined (i.e. needsUsername is false), connect the websocket.
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
	<!-- If guest username is needed, show a username input form -->
	<h2>Kambario kodas: {code}</h2>
	<p>Prašome įvesti vartotojo vardą, kad prisijungtumėte prie kambario</p>
	<input class="border" type="text" bind:value={guestUsername} placeholder="Vartotojo vardas" />
	<button class="border" on:click={submitGuestUsername}>Prisijungti</button>
	{#if errorMessage}
		<p class="error">{errorMessage}</p>
	{/if}
{:else}
	<!-- Otherwise, show the lobby view -->
	<h2>Kambario kodas: {code}</h2>
	<p>Žaidėjai kambaryje:</p>
	<ul>
		{#each players as p}
			<li>{p}</li>
		{/each}
	</ul>
	<button class="border" on:click={leaveLobby}>Palikti kambarį</button>
	{#if errorMessage}
		<p class="error">{errorMessage}</p>
	{/if}
{/if}
