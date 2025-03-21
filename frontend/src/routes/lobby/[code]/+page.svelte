<script>
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	const API_URL = import.meta.env.VITE_API_BASE_URL;

	// Data from the server load function.
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

	// For managing question collections (host only)
	let availableCollections = [];
	let selectedCollections = [];

	// Fetch available question collections (only for host)
	async function fetchAvailableCollections() {
		try {
			const res = await fetch(`${API_URL}/api/available_collections/`);
			if (res.ok) {
				availableCollections = await res.json();
			} else {
				console.error('Failed to fetch available collections');
			}
		} catch (err) {
			console.error('Error fetching available collections:', err);
		}
	}

	// If host, fetch available question collections and initialize selected collections
	if (isHost) {
		fetchAvailableCollections();
		if (lobbyState.question_collections) {
			selectedCollections = lobbyState.question_collections.map((qc) => qc.id);
		}
	}

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
			if (data.players) {
				players = data.players;
			}
			if (data.round_length && data.round_count) {
				roundLength = data.round_length;
				roundCount = data.round_count;
			}
			if (data.question_collections) {
				lobbyState.question_collections = data.question_collections;
				if (isHost) {
					selectedCollections = data.question_collections.map((qc) => qc.id);
				}
			}
			if (data.host_id !== undefined) {
				const newIsHost = parseInt(data.host_id) === parseInt(participantId);
				if (newIsHost && !isHost) {
					isHost = true;
					fetchAvailableCollections();
				} else {
					isHost = newIsHost;
				}
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
			isHost = lobbyState.is_host || false;
			roundLength = lobbyState.round_length || 60;
			roundCount = lobbyState.round_count || 3;
			if (lobbyState.question_collections) {
				selectedCollections = lobbyState.question_collections.map((qc) => qc.id);
			}
			needsUsername = false;
			connectWebSocket();
			if (isHost) {
				fetchAvailableCollections();
			}
		} catch (err) {
			console.error(err);
			errorMessage = 'Serverio klaida bandant prisijungti prie kambario.';
		}
	}

	// Function to leave the lobby.
	async function leaveLobby() {
		try {
			const secret = localStorage.getItem('participantSecret');
			const res = await fetch(`${API_URL}/api/leave_room/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret: secret
				})
			});
			if (!res.ok) {
				const data = await res.json();
				errorMessage = data.error || 'Nepavyko išeiti iš kambario.';
				return;
			}
			localStorage.removeItem('participantId');
			localStorage.removeItem('participantSecret');
			goto('/');
		} catch (err) {
			console.error(err);
			errorMessage = 'Serverio klaida bandant išeiti iš kambario.';
		}
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

	// Host-only: Update question collections.
	async function updateCollections() {
		try {
			const secret = localStorage.getItem('participantSecret');
			const res = await fetch(`${API_URL}/api/update_question_collections/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret,
					collections: selectedCollections
				})
			});
			if (!res.ok) {
				const data = await res.json();
				errorMessage = data.error || 'Nepavyko atnaujinti kolekcijų.';
				return;
			}
			const updated = await res.json();
			lobbyState.question_collections = updated.question_collections;
		} catch (err) {
			console.error(err);
			errorMessage = 'Serverio klaida atnaujinant kolekcijas.';
		}
	}

	// Host-only: Start the game.
	async function startGame() {
		try {
			const secret = localStorage.getItem('participantSecret');
			const res = await fetch(`${API_URL}/api/start_game/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, participant_id: participantId, secret })
			});
			if (!res.ok) {
				const data = await res.json();
				errorMessage = data.error || 'Nepavyko pradėti žaidimo.';
				return;
			}
		} catch (err) {
			console.error(err);
			errorMessage = 'Serverio klaida pradedant žaidimą.';
		}
	}

	let availableCharacters = [];
	let newCharacterName = '';
	let newCharacterDescription = '';

	// Fetch available characters for selection
	async function fetchAvailableCharacters() {
		try {
			const res = await fetch(`${API_URL}/api/available_characters/`);
			if (res.ok) {
				availableCharacters = await res.json();
			}
		} catch (error) {
			console.error('Error fetching characters', error);
		}
	}

	async function selectCharacter(characterId) {
		const secret = localStorage.getItem('participantSecret');
		const res = await fetch(`${API_URL}/api/select_character/`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				code,
				participant_id: participantId,
				secret,
				character_id: characterId
			})
		});
		if (!res.ok) {
			const data = await res.json();
			errorMessage = data.error || 'Nepavyko pasirinkti personažo.';
		}
	}

	async function createCharacter() {
		if (!newCharacterName) {
			errorMessage = 'Įveskite personažo vardą.';
			return;
		}
		const secret = localStorage.getItem('participantSecret');
		const res = await fetch(`${API_URL}/api/create_character/`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				code,
				participant_id: participantId,
				secret,
				name: newCharacterName,
				description: newCharacterDescription
			})
		});
		if (!res.ok) {
			const data = await res.json();
			errorMessage = data.error || 'Nepavyko sukurti personažo.';
		}
	}

	onMount(() => {
		if (!needsUsername) {
			connectWebSocket();
		}
		fetchAvailableCharacters();
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
		{#each players as player}
			<li>
				{player.username}
				{player.characterSelected ? '✅' : ''}
			</li>
		{/each}
	</ul>

	<!-- Display current room settings for all players -->
	<div class="room-settings">
		<h3>Kambario nustatymai</h3>
		<p>Round Length: {roundLength} s</p>
		<p>Round Count: {roundCount}</p>
		{#if lobbyState.question_collections}
			<h4>Pasirinktos klausimų kolekcijos:</h4>
			<ul>
				{#each lobbyState.question_collections as qc}
					<li>{qc.name}</li>
				{/each}
			</ul>
		{/if}
	</div>

	{#if isHost}
		<!-- Host-only controls -->
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

			<!-- Question Collection Management for Host -->
			<h3>Klausimų kolekcijos</h3>
			{#if availableCollections.length > 0}
				{#each availableCollections as collection}
					<div>
						<input
							type="checkbox"
							id="qc-{collection.id}"
							value={collection.id}
							bind:group={selectedCollections}
						/>
						<label for="qc-{collection.id}">{collection.name}</label>
					</div>
				{/each}
				<button class="border" on:click={updateCollections}>Atnaujinti kolekcijas</button>
			{:else}
				<p>Nėra prieinamų klausimų kolekcijų.</p>
			{/if}

			<button class="border" on:click={startGame}>Pradėti žaidimą</button>
		</div>
	{/if}

	{#if !lobbyState.players.find((p) => p.id === participantId)?.characterSelected}
		<h3>Pasirinkite savo personažą</h3>
		<div>
			<h4 class="flex flex-col">Pasirinkti iš esamų:</h4>
			{#each availableCharacters as char}
				<button on:click={() => selectCharacter(char.id)}>{char.name}</button>
			{/each}
		</div>
		<div>
			<h4>Sukurti naują personažą:</h4>
			<input type="text" bind:value={newCharacterName} placeholder="Personažo vardas" />
			<textarea bind:value={newCharacterDescription} placeholder="Aprašymas"></textarea>
			<button on:click={createCharacter}>Sukurti ir pasirinkti</button>
		</div>
	{/if}

	<button class="border" on:click={leaveLobby}>Palikti kambarį</button>
	{#if errorMessage}
		<p class="error">{errorMessage}</p>
	{/if}
{/if}
