<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	const API_URL = import.meta.env.VITE_API_BASE_URL;

	let code;
	$: code = $page.params.code; // Extract from route param

	let players = [];
	let errorMessage = '';

	let socket;

	onMount(() => {
		connectWebSocket();
	});

	function connectWebSocket() {
		// Fallback if API_URL is undefined for any reason
		let baseUrl = API_URL || 'http://localhost:8000';

		// Convert http(s) -> ws(s)
		if (baseUrl.startsWith('https://')) {
			baseUrl = baseUrl.replace('https://', 'wss://');
		} else if (baseUrl.startsWith('http://')) {
			baseUrl = baseUrl.replace('http://', 'ws://');
		}

		const wsUrl = `${baseUrl}/ws/lobby/${code}/`;

		socket = new WebSocket(wsUrl);

		socket.onopen = () => {
			console.log(`Connected to lobby: ${code}`);
		};

		socket.onerror = (event) => {
			console.error('WebSocket error:', event);
			errorMessage = 'Nepavyko prisijungti prie WS.';
		};

		socket.onmessage = (event) => {
			const data = JSON.parse(event.data);
			// Expecting data to have "players", "status", etc.
			if (data.players) {
				players = data.players;
			}
		};
	}
	function leaveLobby() {
		// You could also call an API to remove the participant,
		// but for now let's just close the WS and go home.
		if (socket) {
			socket.close();
		}
		goto('/');
	}
</script>

<h2>Kambario kodas: {code}</h2>

<p>Žaidėjai kambaryje:</p>
<ul>
	{#each players as p}
		<li>{p}</li>
	{/each}
</ul>

<button class="border" on:click={leaveLobby}> Palikti kambarį </button>

{#if errorMessage}
	<p class="error">{errorMessage}</p>
{/if}
