<!-- src/routes/lobby/[code]/+page.svelte -->
<script>
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { toast } from '@zerodevx/svelte-toast';
	import { toastOptions } from '$lib/toastConfig';
	import { apiFetch } from '$lib/api';
	import { user } from '$lib/stores/auth';
	import { get } from 'svelte/store';
	import { ProgressRing } from '@skeletonlabs/skeleton-svelte';

	// Child components
	import GuestUsernameForm from './components/GuestUsernameForm.svelte';
	import LobbyPending from './components/LobbyPending.svelte';
	import LobbyInProgress from './components/LobbyInProgress.svelte';
	import LobbyGuessing from './components/LobbyGuessing.svelte';
	import LobbyCompleted from './components/LobbyCompleted.svelte';

	export let data;
	const { roomCode, lobbyState: initialState } = data;

	// local reactive copies
	let needsUsernameLocal = false;
	let code = needsUsernameLocal ? roomCode : initialState.code;
	let lobbyState = needsUsernameLocal ? {} : { ...initialState };
	let players = !needsUsernameLocal ? lobbyState.players || [] : [];
	let myCharacter = null;

	// participant creds
	let participantId = lobbyState.participant_id;
	let participantSecret = lobbyState.secret;

	if (browser) {
		// clear old creds if we switched rooms
		const storedRoom = sessionStorage.getItem('roomCode');
		if (storedRoom !== code) {
			sessionStorage.removeItem('participantId');
			sessionStorage.removeItem('participantSecret');
		}
		sessionStorage.setItem('roomCode', code);

		// load any already‐stored creds
		const storedId = sessionStorage.getItem('participantId');
		const storedSecret = sessionStorage.getItem('participantSecret');
		if (storedId && storedSecret) {
			participantId = storedId;
			participantSecret = storedSecret;
			needsUsernameLocal = false; // we already have a guest identity
		} else if (!get(user) && initialState.status === 'pending') {
			// first‐time guest in a pending room needs to pick a name
			needsUsernameLocal = true;
		}
		const storedName = sessionStorage.getItem('myCharacterName');
		const storedImage = sessionStorage.getItem('myCharacterImage');
		if (storedName) {
			myCharacter = { name: storedName, image: storedImage || null };
		}
	}

	// lobby settings
	$: isHost = lobbyState.is_host || false;
	let roundLength = lobbyState?.round_length || 60;
	let roundCount = lobbyState?.round_count || 3;
	let guessTimer = lobbyState?.guess_timer || 60;

	// for host
	let availableCollections = [];
	let selectedCollections = lobbyState.question_collections?.map((q) => q.id) || [];
	let availableCharacters = [];
	let newCharacterName = '';
	let newCharacterDescription = '';
	let newCharacterImage = null;

	// chat & rounds
	let chatMessages = lobbyState.messages || [];
	let chatInput = '';
	let currentRound = lobbyState.current_round || {
		round_number: null,
		question: '',
		end_time: null
	};
	let timeLeft = 0;
	let timerInterval;

	// guessing phase
	let guessOptions = [];
	let guessMap = {};
	let guessTimeLeft = 0;
	let guessTimerInterval;

	// WS + heartbeat
	let socket;
	let heartbeatInterval;

	let isLoading = true;
	onMount(() => {
		isLoading = false;
		const isLoggedIn = !!get(user);

		if (isLoggedIn) {
			// Authenticated user: auto‐join via token (which in turn calls connectWebSocket())
			joinAsAuthenticated();
		} else if (!needsUsernameLocal && participantId && participantSecret) {
			// We already have guest creds in sessionStorage: rejoin and open socket there
			rejoinRoom();
		}
		// Otherwise: first‐time guest => show username form, wait until submitGuestUsername() calls rejoinRoom()

		// Meanwhile we can still fetch these for the host later
		fetchAvailableCollections();
		fetchAvailableCharacters();
		timerInterval = setInterval(updateTimeLeft, 1000);
		guessTimerInterval = setInterval(updateGuessTimeLeft, 1000);
	});

	onDestroy(() => {
		clearInterval(timerInterval);
		clearInterval(guessTimerInterval);
		if (heartbeatInterval) clearInterval(heartbeatInterval);
		if (socket) socket.close();
	});

	async function joinAsAuthenticated() {
		try {
			const res = await apiFetch('/api/join_room/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code })
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(
					err.error ?? 'Nepavyko prisijungti kaip prisijungęs vartotojas.',
					toastOptions.error
				);
				return setTimeout(() => goto('/'), 2000);
			}
			const data = await res.json();
			lobbyState = data;
			players = data.players || [];
			participantId = data.participant_id;
			participantSecret = data.secret;
			sessionStorage.setItem('participantId', participantId);
			sessionStorage.setItem('participantSecret', participantSecret);
			needsUsernameLocal = false;
			connectWebSocket();
			if (data.is_host) fetchAvailableCollections();
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida prisijungiant kaip vartotojas.', toastOptions.error);
		}
	}

	// skip the initial lobby dump
	let firstLobbyMessage = true;

	function connectWebSocket() {
		if (socket?.readyState === WebSocket.OPEN) return;

		let base = import.meta.env.VITE_API_BASE_URL;
		if (base.startsWith('https://')) base = base.replace('https://', 'wss://');
		else if (base.startsWith('http://')) base = base.replace('http://', 'ws://');

		socket = new WebSocket(`${base}/ws/lobby/${code}/`);

		socket.onopen = () => {
			heartbeatInterval = setInterval(() => {
				if (socket.readyState === WebSocket.OPEN) {
					socket.send(JSON.stringify({ type: 'ping', participant_id: participantId }));
				}
			}, 15000);
		};

		socket.onerror = () => {
			toast.push('Nepavyko prisijungti prie WS.', toastOptions.error);
		};

		socket.onmessage = ({ data }) => {
			const msg = JSON.parse(data);

			if (msg.status) {
				lobbyState.status = msg.status;
			}

			// Full lobby update
			if (msg.players) {
				players = msg.players;

				if (firstLobbyMessage) {
					// skip kick-check on the very first lobby state
					firstLobbyMessage = false;
				} else {
					if (!players.some((p) => String(p.id) === String(participantId))) {
						sessionStorage.removeItem('participantId');
						sessionStorage.removeItem('participantSecret');

						toast.push('Buvai išmestas iš kambario.', toastOptions.error);
						goto('/');
						return;
					}
				}
			}

			// Game settings update
			if (msg.round_length && msg.round_count) {
				roundLength = msg.round_length;
				roundCount = msg.round_count;
			}

			if (msg.guess_timer !== undefined) {
				guessTimer = msg.guess_timer;
			}
			if (msg.guess_deadline !== undefined) {
				lobbyState.guess_deadline = msg.guess_deadline;
			}
			if (msg.question_collections) {
				lobbyState.question_collections = msg.question_collections;
				selectedCollections = msg.question_collections.map((q) => q.id);
			}
			if (msg.host_id !== undefined) {
				isHost = +msg.host_id === +participantId;
				if (isHost) fetchAvailableCollections();
			}

			// Chat & round updates
			if (msg.type === 'chat_update' && msg.message) {
				chatMessages = [...chatMessages, msg.message];
			}
			if (msg.type === 'round_update' && msg.round) {
				currentRound = msg.round;
				if (msg.status) lobbyState.status = msg.status;
			}
		};

		socket.onclose = () => {};
	}

	async function rejoinRoom() {
		try {
			const res = await apiFetch('/api/join_room/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, participant_id: participantId, secret: participantSecret })
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.error ?? 'Nepavyko atkurti ryšio.', toastOptions.error);
				return setTimeout(() => goto('/'), 3000);
			}
			const data = await res.json();
			lobbyState = data;
			players = data.players || [];
			roundLength = data.round_length || 60;
			roundCount = data.round_count || 3;
			guessTimer = data.guess_timer || 60;
			participantId = data.participant_id;
			participantSecret = data.secret;
			sessionStorage.setItem('participantId', participantId);
			sessionStorage.setItem('participantSecret', participantSecret);
			if (data.current_round) currentRound = data.current_round;
			if (data.messages) chatMessages = data.messages;
			if (data.question_collections)
				selectedCollections = data.question_collections.map((q) => q.id);
			connectWebSocket();
			isHost = data.is_host;
			if (isHost) fetchAvailableCollections();
			needsUsernameLocal = false;
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
			setTimeout(() => goto('/'), 3000);
		}
	}

	async function fetchAvailableCollections() {
		try {
			const res = await apiFetch('/api/available_collections/');
			if (res.ok) availableCollections = await res.json();
		} catch {}
	}

	async function fetchAvailableCharacters() {
		try {
			const res = await apiFetch('/api/available_characters/');
			if (res.ok) availableCharacters = await res.json();
		} catch {}
	}

	function updateTimeLeft() {
		if (currentRound.end_time) {
			const end = new Date(currentRound.end_time);
			timeLeft = Math.max(0, Math.floor((end - Date.now()) / 1000));
		}
	}
	function updateGuessTimeLeft() {
		if (lobbyState.guess_deadline) {
			const dl = new Date(lobbyState.guess_deadline);
			guessTimeLeft = Math.max(0, Math.floor((dl - Date.now()) / 1000));
		}
	}

	async function submitGuestUsername(event) {
		const { guestUsername } = event.detail;
		if (!guestUsername) {
			toast.push('Įveskite vardą.', toastOptions.error);
			return;
		}
		try {
			const res = await apiFetch('/api/join_room/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, guest_username: guestUsername })
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.error ?? 'Nepavyko prisijungti.', toastOptions.error);
				return;
			}
			const data = await res.json();
			lobbyState = data;
			players = data.players || [];
			participantId = data.participant_id;
			participantSecret = data.secret;
			sessionStorage.setItem('participantId', participantId);
			sessionStorage.setItem('participantSecret', participantSecret);
			needsUsernameLocal = false;
			connectWebSocket();
			if (data.is_host) fetchAvailableCollections();
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida prisijungiant į kambarį.', toastOptions.error);
		}
	}

	async function leaveLobby() {
		if (socket && socket.readyState === WebSocket.OPEN) {
			socket.close();
		}

		try {
			const res = await apiFetch('/api/leave_room/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, participant_id: participantId, secret: participantSecret })
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				return toast.push(err.error ?? 'Nepavyko išeiti.', toastOptions.error);
			}
			sessionStorage.removeItem('participantId');
			sessionStorage.removeItem('participantSecret');
			goto('/');
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		}
	}

	async function updateSettings(e) {
		const { roundLength: rL, roundCount: rC, guessTimer: gT, selectedCollections: sC } = e.detail;
		try {
			const res = await apiFetch('/api/update_settings/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret: participantSecret,
					round_length: rL,
					round_count: rC,
					guess_timer: gT,
					selectedCollections: sC
				})
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				return toast.push(err.error ?? 'Nepavyko atnaujinti.', toastOptions.error);
			}
			const upd = await res.json();
			roundLength = upd.round_length;
			roundCount = upd.round_count;
			guessTimer = upd.guess_timer;
			toast.push('Nustatymai atnaujinti!', toastOptions.success);
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		}
	}

	async function updateCollections(e) {
		try {
			const res = await apiFetch('/api/update_question_collections/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret: participantSecret,
					collections: e.detail.collections
				})
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				return toast.push(err.error ?? 'Nepavyko atnaujinti kolekcijų.', toastOptions.error);
			}
			const upd = await res.json();
			lobbyState.question_collections = upd.question_collections;
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		}
	}

	async function startGame() {
		try {
			const res = await apiFetch('/api/start_game/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, participant_id: participantId, secret: participantSecret })
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.error ?? 'Nepavyko pradėti žaidimo.', toastOptions.error);
			}
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		}
	}

	async function selectCharacter(e) {
		const { characterId } = e.detail;
		try {
			const res = await apiFetch('/api/select_character/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret: participantSecret,
					character_id: characterId
				})
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.error ?? 'Nepavyko pasirinkti personažo.', toastOptions.error);
			} else {
				const char = availableCharacters.find((c) => c.id === characterId);
				if (char) {
					myCharacter = { name: char.name, image: char.image || null };
					if (browser) {
						sessionStorage.setItem('myCharacterName', char.name);
						sessionStorage.setItem('myCharacterImage', char.image || '');
					}
				}
				toast.push('Personažas pasirinktas!', toastOptions.success);
			}
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		}
	}

	async function createCharacter(e) {
		const { name, description, image } = e.detail;
		if (!name) return toast.push('Įveskite vardą.', toastOptions.error);
		const form = new FormData();
		form.append('code', code);
		form.append('participant_id', participantId);
		form.append('secret', participantSecret);
		form.append('name', name);
		form.append('description', description || '');
		if (image) form.append('image', image);
		try {
			const res = await apiFetch('/api/create_character/', { method: 'POST', body: form });
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.error ?? 'Nepavyko sukurti personažo.', toastOptions.error);
			} else {
				myCharacter = { name, image: image ? URL.createObjectURL(image) : null };
				if (browser) {
					sessionStorage.setItem('myCharacterName', name);
					sessionStorage.setItem('myCharacterImage', myCharacter.image || '');
				}
				toast.push('Personažas sukurtas!', toastOptions.success);
			}
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		}
	}

	async function sendChatMessage(e) {
		const text = e.detail.text.trim();
		if (!text) return;
		try {
			const res = await apiFetch('/api/send_chat_message/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret: participantSecret,
					text
				})
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.error ?? 'Nepavyko siųsti žinutės.', toastOptions.error);
			}
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		}
	}

	async function fetchGuessOptions() {
		try {
			const url = `/api/available_guess_options/?code=${encodeURIComponent(code)}&participant_id=${participantId}&secret=${participantSecret}`;
			const res = await apiFetch(url);
			if (res.ok) guessOptions = await res.json();
		} catch {}
	}

	$: if (lobbyState.status === 'guessing') fetchGuessOptions();

	async function submitGuesses() {
		const guessesArray = [];
		for (const p of players) {
			if (`${p.id}` === `${participantId}`) continue;
			const g = guessMap[p.id];
			if (g)
				guessesArray.push({
					guessed_participant_id: p.id,
					guessed_character_id: +g
				});
		}
		try {
			const res = await apiFetch('/api/submit_guesses/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret: participantSecret,
					guesses: guessesArray
				})
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.error ?? 'Nepavyko pateikti spėjimų.', toastOptions.error);
			}
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		}
	}

	async function addNpc() {
		try {
			const res = await apiFetch('/api/add_npc/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret: participantSecret
				})
			});
			const data = await res.json().catch(() => ({}));
			if (!res.ok) {
				toast.push(data.error ?? 'Nepavyko pridėti NPC.', toastOptions.error);
			} else {
				toast.push('AI žaidėjas pridėtas!', toastOptions.success);
			}
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida pridedant NPC.', toastOptions.error);
		}
	}

	async function kickPlayer(event) {
		const { id, username } = event.detail;
		try {
			const res = await apiFetch('/api/kick_player/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret: participantSecret,
					target_participant_id: id
				})
			});
			const data = await res.json().catch(() => ({}));
			if (!res.ok) {
				toast.push(data.error || `Nepavyko išmesti ${username}`, toastOptions.error);
			} else {
				toast.push(`Žaidėjas ${username} buvo išmestas iš kambario`, toastOptions.success);
			}
		} catch (e) {
			console.error(e);
			toast.push(`Serverio klaida išmetant ${username}`, toastOptions.error);
		}
	}
</script>

{#if isLoading}
	<ProgressRing
		value={null}
		size="size-14"
		meterStroke="stroke-primary-600-400"
		trackStroke="stroke-surface-200-800"
	/>
{:else if needsUsernameLocal && !get(user)}
	<GuestUsernameForm {code} on:submitGuestUsername={submitGuestUsername} />
{:else if lobbyState.status === 'pending'}
	<LobbyPending
		{code}
		{lobbyState}
		{players}
		{isHost}
		{roundLength}
		{roundCount}
		{guessTimer}
		{availableCollections}
		{selectedCollections}
		{availableCharacters}
		bind:newCharacterName
		bind:newCharacterDescription
		bind:newCharacterImage
		on:updateSettings={updateSettings}
		on:updateCollections={updateCollections}
		on:startGame={startGame}
		on:selectCharacter={selectCharacter}
		on:createCharacter={createCharacter}
		on:addNpc={addNpc}
		on:kickPlayer={kickPlayer}
		on:leaveLobby={leaveLobby}
	/>
{:else if lobbyState.status === 'in_progress'}
	<LobbyInProgress
		{currentRound}
		{timeLeft}
		{chatMessages}
		{myCharacter}
		bind:chatInput
		on:sendChatMessage={sendChatMessage}
		on:leaveLobby={leaveLobby}
	/>
{:else if lobbyState.status === 'guessing'}
	<LobbyGuessing
		{guessTimeLeft}
		{players}
		{participantId}
		{guessOptions}
		{guessMap}
		on:submitGuesses={submitGuesses}
		on:leaveLobby={leaveLobby}
	/>
{:else if lobbyState.status === 'completed'}
	<LobbyCompleted {players} currentUserId={participantId} on:leaveLobby={leaveLobby} />
{/if}
