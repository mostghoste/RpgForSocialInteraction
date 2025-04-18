<!-- src/routes/lobby/[code]/+page.svelte -->
<script>
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { toast } from '@zerodevx/svelte-toast';
	import { toastOptions } from '$lib/toastConfig';

	// Child components
	import GuestUsernameForm from './components/GuestUsernameForm.svelte';
	import LobbyPending from './components/LobbyPending.svelte';
	import LobbyInProgress from './components/LobbyInProgress.svelte';
	import LobbyGuessing from './components/LobbyGuessing.svelte';
	import LobbyCompleted from './components/LobbyCompleted.svelte';

	export let data;
	const API_URL = import.meta.env.VITE_API_BASE_URL;

	// Main reactive data
	let needsUsername = data.needsUsername;
	let code = needsUsername ? data.roomCode : data.lobbyState.code;
	let lobbyState = needsUsername ? {} : data.lobbyState;
	let players = needsUsername ? [] : lobbyState.players || [];

	// Credentials
	let participantId = lobbyState?.participant_id;
	let participantSecret = lobbyState?.secret;

	if (browser) {
		if (participantId) sessionStorage.setItem('participantId', participantId);
		else participantId = sessionStorage.getItem('participantId');

		if (participantSecret) sessionStorage.setItem('participantSecret', participantSecret);
		else participantSecret = sessionStorage.getItem('participantSecret');
	}

	$: isHost = lobbyState.is_host || false;
	let roundLength = lobbyState?.round_length || 60;
	let roundCount = lobbyState?.round_count || 3;
	let guessTimer = lobbyState?.guess_timer || 60;

	let availableCollections = [];
	let selectedCollections = lobbyState?.question_collections
		? lobbyState.question_collections.map((qc) => qc.id)
		: [];
	let availableCharacters = [];
	let newCharacterName = '';
	let newCharacterDescription = '';
	let newCharacterImage;

	let chatMessages = lobbyState.messages || [];
	let chatInput = '';

	let currentRound = lobbyState.current_round || {
		round_number: null,
		question: '',
		end_time: null
	};
	let timeLeft = 0;
	let timerInterval;

	let guessOptions = [];
	let guessMap = {};
	let guessTimeLeft = 0;
	let guessTimerInterval;

	let socket;
	let heartbeatInterval;

	onMount(() => {
		const storedRoom = sessionStorage.getItem('roomCode');
		if (storedRoom !== code) {
			sessionStorage.removeItem('participantId');
			sessionStorage.removeItem('participantSecret');
		}

		if (sessionStorage.getItem('participantId') && sessionStorage.getItem('participantSecret')) {
			rejoinRoom();
		} else {
			connectWebSocket();
		}
		fetchAvailableCharacters();

		timerInterval = setInterval(updateTimeLeft, 1000);
		guessTimerInterval = setInterval(updateGuessTimeLeft, 1000);
	});

	onDestroy(() => {
		if (heartbeatInterval) clearInterval(heartbeatInterval);
		if (socket) socket.close();
		clearInterval(timerInterval);
		clearInterval(guessTimerInterval);
	});

	function connectWebSocket() {
		if (socket && socket.readyState === WebSocket.OPEN) return;

		let baseUrl = API_URL || 'http://localhost:8000';
		if (baseUrl.startsWith('https://')) {
			baseUrl = baseUrl.replace('https://', 'wss://');
		} else if (baseUrl.startsWith('http://')) {
			baseUrl = baseUrl.replace('http://', 'ws://');
		}

		socket = new WebSocket(`${baseUrl}/ws/lobby/${code}/`);

		socket.onopen = () => {
			heartbeatInterval = setInterval(() => {
				if (socket.readyState === WebSocket.OPEN) {
					socket.send(JSON.stringify({ type: 'ping', participant_id: participantId }));
				}
			}, 15000);
		};

		socket.onerror = (event) => {
			console.error('WebSocket error:', event);
			toast.push('Nepavyko prisijungti prie WS.', toastOptions.error);
		};

		socket.onmessage = (event) => {
			const data = JSON.parse(event.data);
			if (data.status) lobbyState.status = data.status;
			if (data.players) players = data.players;
			if (data.round_length && data.round_count) {
				roundLength = data.round_length;
				roundCount = data.round_count;
			}
			if (data.guess_timer !== undefined) guessTimer = data.guess_timer;
			if (data.guess_deadline !== undefined) lobbyState.guess_deadline = data.guess_deadline;
			if (data.question_collections) {
				lobbyState.question_collections = data.question_collections;
				selectedCollections = data.question_collections.map((qc) => qc.id);
			}
			if (data.host_id !== undefined) {
				isHost = parseInt(data.host_id) === parseInt(participantId);
				if (isHost) fetchAvailableCollections();
			}
			if (data.type === 'chat_update' && data.message) {
				chatMessages = [...chatMessages, data.message];
			}
			if (data.type === 'round_update' && data.round) {
				currentRound = data.round;
				if (data.status) {
					lobbyState.status = data.status;
				}
			}
		};

		socket.onclose = (event) => {
			console.log('WebSocket disconnected:', event.code, event.reason);
		};
	}

	async function rejoinRoom() {
		try {
			const storedId = sessionStorage.getItem('participantId');
			const storedSecret = sessionStorage.getItem('participantSecret');
			const res = await fetch(`${API_URL}/api/join_room/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, participant_id: storedId, secret: storedSecret })
			});
			if (res.ok) {
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
				if (data.question_collections) {
					selectedCollections = data.question_collections.map((qc) => qc.id);
				}
				connectWebSocket();
				isHost = data.is_host;
				if (isHost) fetchAvailableCollections();
				needsUsername = false;
			} else {
				const errorData = await res.json().catch(() => ({}));
				toast.push(errorData.error || 'Nepavyko atkurti ryšio.', toastOptions.error);
				setTimeout(() => goto('/'), 3000);
			}
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida bandant atkurti ryšį.', toastOptions.error);
			setTimeout(() => goto('/'), 3000);
		}
	}

	async function fetchAvailableCollections() {
		try {
			const res = await fetch(`${API_URL}/api/available_collections/`);
			if (res.ok) {
				availableCollections = await res.json();
			}
		} catch (err) {
			console.error('Error fetching available collections:', err);
		}
	}

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

	function updateTimeLeft() {
		if (currentRound.end_time) {
			const endTime = new Date(currentRound.end_time);
			timeLeft = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
		}
	}

	function updateGuessTimeLeft() {
		if (lobbyState.guess_deadline) {
			const deadline = new Date(lobbyState.guess_deadline);
			guessTimeLeft = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
		}
	}

	async function submitGuestUsername(event) {
		const { guestUsername } = event.detail;
		if (!guestUsername) {
			toast.push('Prašome įvesti vartotojo vardą.', toastOptions.error);
			return;
		}
		try {
			const res = await fetch(`${API_URL}/api/join_room/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, guest_username: guestUsername })
			});
			if (!res.ok) {
				const data = await res.json().catch(() => ({}));
				toast.push(data.error ?? 'Nepavyko prisijungti.', toastOptions.error);
				return;
			}
			const data = await res.json();
			lobbyState = data;
			players = data.players || [];
			participantId = data.participant_id;
			participantSecret = data.secret;
			if (browser && participantId) {
				sessionStorage.setItem('participantId', participantId);
				sessionStorage.setItem('participantSecret', participantSecret);
				sessionStorage.setItem('roomCode', code);
			}
			isHost = data.is_host || false;
			roundLength = data.round_length || 60;
			roundCount = data.round_count || 3;
			guessTimer = data.guess_timer || 60;
			if (data.question_collections) {
				selectedCollections = data.question_collections.map((qc) => qc.id);
			}
			needsUsername = false;
			connectWebSocket();
			if (isHost) fetchAvailableCollections();
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida bandant prisijungti prie kambario.', toastOptions.error);
		}
	}

	async function leaveLobby() {
		try {
			const secret = sessionStorage.getItem('participantSecret');
			const res = await fetch(`${API_URL}/api/leave_room/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, participant_id: participantId, secret })
			});
			if (!res.ok) {
				const data = await res.json().catch(() => ({}));
				toast.push(data.error || 'Nepavyko išeiti iš kambario.', toastOptions.error);
				return;
			}
			sessionStorage.removeItem('participantId');
			sessionStorage.removeItem('participantSecret');
			goto('/');
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida bandant išeiti iš kambario.', toastOptions.error);
		}
	}

	async function updateSettings(event) {
		const {
			roundLength: newRL,
			roundCount: newRC,
			guessTimer: newGT,
			selectedCollections: newSC
		} = event.detail;
		try {
			const secret = sessionStorage.getItem('participantSecret');
			const res = await fetch(`${API_URL}/api/update_settings/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret,
					round_length: newRL,
					round_count: newRC,
					guess_timer: newGT,
					selectedCollections: newSC
				})
			});
			if (!res.ok) {
				const data = await res.json();
				toast.push(data.error || 'Nepavyko atnaujinti nustatymų.', toastOptions.error);
				return;
			}
			const updated = await res.json();
			roundLength = updated.round_length;
			roundCount = updated.round_count;
			guessTimer = updated.guess_timer;
			toast.push('Nustatymai atnaujinti sėkmingai!', toastOptions.success);
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida atnaujinant nustatymus.', toastOptions.error);
		}
	}

	async function updateCollections(event) {
		try {
			const secret = sessionStorage.getItem('participantSecret');
			const res = await fetch(`${API_URL}/api/update_question_collections/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret,
					collections: event.detail.collections
				})
			});
			if (!res.ok) {
				const data = await res.json().catch(() => ({}));
				toast.push(data.error || 'Nepavyko atnaujinti kolekcijų.', toastOptions.error);
				return;
			}
			const updated = await res.json();
			lobbyState.question_collections = updated.question_collections;
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida atnaujinant kolekcijas.', toastOptions.error);
		}
	}

	async function startGame() {
		try {
			const secret = sessionStorage.getItem('participantSecret');
			const res = await fetch(`${API_URL}/api/start_game/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ code, participant_id: participantId, secret })
			});
			if (!res.ok) {
				const data = await res.json().catch(() => ({}));
				toast.push(data.error || 'Nepavyko pradėti žaidimo.', toastOptions.error);
				return;
			}
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida pradedant žaidimą.', toastOptions.error);
		}
	}

	async function selectCharacter(event) {
		const { characterId } = event.detail;
		const secret = sessionStorage.getItem('participantSecret');
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
			const data = await res.json().catch(() => ({}));
			toast.push(data.error || 'Nepavyko pasirinkti personažo.', toastOptions.error);
		} else {
			toast.push('Personažas sėkmingai pasirinktas!', toastOptions.success);
		}
	}

	async function createCharacter(event) {
		const { name, description, image } = event.detail;
		if (!name) {
			toast.push('Įveskite personažo vardą.', toastOptions.error);
			return;
		}
		const secret = sessionStorage.getItem('participantSecret');
		const formData = new FormData();
		formData.append('code', code);
		formData.append('participant_id', participantId);
		formData.append('secret', secret);
		formData.append('name', name);
		formData.append('description', description || '');
		if (image) formData.append('image', image);

		const res = await fetch(`${API_URL}/api/create_character/`, {
			method: 'POST',
			body: formData
		});
		if (!res.ok) {
			const data = await res.json().catch(() => ({}));
			toast.push(data.error || 'Nepavyko sukurti personažo.', toastOptions.error);
		} else {
			toast.push('Personažas sėkmingai sukurtas ir pasirinktas!', toastOptions.success);
		}
	}

	async function sendChatMessage(event) {
		const { text } = event.detail;
		const trimmed = text.trim();
		if (!trimmed) return;
		try {
			const res = await fetch(`${API_URL}/api/send_chat_message/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					code,
					participant_id: participantId,
					secret: participantSecret,
					text: trimmed
				})
			});
			if (!res.ok) {
				const data = await res.json().catch(() => ({}));
				toast.push(data.error || 'Nepavyko išsiųsti žinutės.', toastOptions.error);
			}
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida siunčiant žinutę.', toastOptions.error);
		}
	}

	async function fetchGuessOptions() {
		try {
			const res = await fetch(
				`${API_URL}/api/available_guess_options/?code=${encodeURIComponent(code)}&participant_id=${participantId}&secret=${participantSecret}`
			);

			if (res.ok) {
				guessOptions = await res.json();
			} else {
				console.error('Nepavyko gauti kitų žaidėjų veikėjų.');
			}
		} catch (err) {
			console.error('Nepavyko gauti kitų žaidėjų veikėjų:', err);
		}
	}

	$: if (lobbyState.status === 'guessing') {
		fetchGuessOptions();
	}

	async function submitGuesses() {
		const guessesArray = [];
		for (const player of players) {
			if (String(player.id) === String(participantId)) continue;
			const guessedCharId = guessMap[player.id];
			if (guessedCharId) {
				guessesArray.push({
					guessed_participant_id: player.id,
					guessed_character_id: parseInt(guessedCharId, 10)
				});
			}
		}
		try {
			const res = await fetch(`${API_URL}/api/submit_guesses/`, {
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
				const data = await res.json().catch(() => ({}));
				toast.push(data.error || 'Nepavyko pateikti spėjimų.', toastOptions.error);
			}
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida teikiant spėjimus.', toastOptions.error);
		}
	}
</script>

{#if needsUsername}
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
		on:leaveLobby={leaveLobby}
	/>
{:else if lobbyState.status === 'in_progress'}
	<LobbyInProgress
		{API_URL}
		{currentRound}
		{timeLeft}
		{chatMessages}
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
