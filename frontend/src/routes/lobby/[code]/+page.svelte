<script>
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	const API_URL = import.meta.env.VITE_API_BASE_URL;

	// The lobby state is loaded from the server load function.
	export let data;
	let { lobbyState } = data;

	// Extract the room code from the loaded data (or from the URL)
	let code = lobbyState.code;
	let players = lobbyState.players || [];
	let errorMessage = '';

	let socket;
	let heartbeatInterval;

	// Store the participant_id from the join endpoint if not already stored.
	let participantId = lobbyState.participant_id;
	if (participantId) {
		localStorage.setItem('participantId', participantId);
	} else {
		participantId = localStorage.getItem('participantId');
	}

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
			// Start heartbeat: ping every 15 seconds
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

	function leaveLobby() {
		if (socket) {
			socket.close();
		}
		// Optionally, call a leave endpoint to remove participant.
		goto('/');
	}

	onMount(() => {
		connectWebSocket();
	});

	onDestroy(() => {
		if (heartbeatInterval) clearInterval(heartbeatInterval);
		if (socket) socket.close();
	});
</script>

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
