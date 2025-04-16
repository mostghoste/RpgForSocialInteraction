<script>
	import { onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';

	// Expects "players" passed in with extra fields:
	// - assigned_character: { name, image? }
	// - correctGuesses: number
	// - guesses: an array of objects with { guesser_id, guessed_character_name, is_correct }
	export let players = [];
	export let currentUserId;

	const dispatch = createEventDispatcher();

	// These arrays will be populated gradually:
	let revealedPlayers = [];
	let revealedPodium = [];

	let phase = 'identity'; // phases: 'identity', 'podium', 'final'
	const identityDelay = 3000;
	const podiumDelay = 3000;
	const podiumItemDelay = 3000;
	let podiumPlayers = [];

	// Gradually reveal player identities.
	function revealIdentities() {
		players.forEach((player, index) => {
			setTimeout(
				() => {
					revealedPlayers = [...revealedPlayers, player];
					if (index === players.length - 1) {
						setTimeout(() => {
							startPodiumReveal();
						}, podiumDelay);
					}
				},
				identityDelay * (index + 1)
			);
		});
	}

	// Start the podium reveal (top 3 players).
	function startPodiumReveal() {
		podiumPlayers = [...players].sort((a, b) => b.points - a.points).slice(0, 3);
		let order =
			podiumPlayers.length === 3
				? [podiumPlayers[2], podiumPlayers[1], podiumPlayers[0]]
				: podiumPlayers;
		order.forEach((player, index) => {
			setTimeout(
				() => {
					revealedPodium = [...revealedPodium, player];
					if (index === order.length - 1) {
						setTimeout(() => {
							phase = 'final';
						}, podiumItemDelay);
					}
				},
				podiumItemDelay * (index + 1)
			);
		});
		phase = 'podium';
	}

	// Helper to return the guess from the current user from a list of guesses.
	function getMyGuess(guesses) {
		if (!guesses) return null;
		return guesses.find((g) => g.guesser_id === currentUserId);
	}

	onMount(() => {
		revealIdentities();
	});

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}
</script>

<Banner>
	<h2 class="h3">Žaidimas baigėsi!</h2>
</Banner>

<main class="flex h-full w-full flex-col items-center justify-center gap-4 overflow-y-scroll">
	{#if phase === 'identity'}
		<h3 class="mb-4 text-3xl font-bold">Identitetų atskleidimas...</h3>
		<div class="grid w-full max-w-xl gap-4">
			{#each revealedPlayers as player (player.id)}
				<div class="rounded-lg border p-4 shadow">
					<div class="flex items-center justify-between">
						<div class="flex flex-col">
							<h4 class="text-xl font-bold">
								{player.username}{player.is_host ? ' 👑' : ''}
							</h4>
							{#if player.assigned_character}
								<p class="text-md">
									Personažas: {player.assigned_character.name}
								</p>
							{:else}
								<p class="text-md italic">Nėra pasirinkto personažo</p>
							{/if}
						</div>
						{#if player.assigned_character && player.assigned_character.image}
							<img
								src={player.assigned_character.image}
								alt={player.assigned_character.name}
								class="h-16 w-16 rounded-full object-cover"
							/>
						{/if}
					</div>
					<p class="text-md mt-2">
						{player.correctGuesses} iš {players.length - 1} žaidėjų atspėjo!
					</p>
					{#if player.guesses}
						{#if getMyGuess(player.guesses)}
							<p class="text-md mt-1">
								Tavo spėjimas:
								<span
									class={getMyGuess(player.guesses).is_correct ? 'text-green-500' : 'text-red-500'}
								>
									{getMyGuess(player.guesses).guessed_character_name}
								</span>
							</p>
						{:else}
							<p class="text-md mt-1">
								Tavo spėjimas:
								<span class="text-red-500"> Neatlikai spėjimo šiam žaidėjui </span>
							</p>
						{/if}
					{/if}
				</div>
			{/each}
		</div>
	{:else if phase === 'podium'}
		<h3 class="mb-4 text-3xl font-bold">Podiumas</h3>
		<div class="flex flex-col items-center gap-4">
			{#each revealedPodium as player, i (player.id)}
				<div class="flex w-full max-w-md items-center gap-4 rounded-lg border p-4 shadow">
					<div class="text-2xl font-bold">
						{podiumPlayers.length === 3
							? i === 0
								? '3. vieta'
								: i === 1
									? '2. vieta'
									: '1. vieta'
							: i + 1 + '.'}
					</div>
					<div class="flex flex-col">
						<h4 class="text-xl font-bold">{player.username}</h4>
						<p class="text-md">Taškai: {player.points}</p>
					</div>
				</div>
			{/each}
		</div>
	{:else if phase === 'final'}
		<h3 class="mb-4 text-3xl font-bold">Pilni rezultatai</h3>
		<div class="grid w-full max-w-xl gap-4">
			{#each players as player (player.id)}
				<div
					class="rounded-lg border p-4 shadow {player.myGuessCorrect
						? 'border-green-500'
						: 'border-gray-300'}"
				>
					<div class="flex items-center justify-between">
						<div class="flex flex-col">
							<h4 class="text-xl font-bold">
								{player.username}{player.is_host ? ' 👑' : ''}
							</h4>
							{#if player.assigned_character}
								<p class="text-md">
									Personažas: {player.assigned_character.name}
								</p>
							{:else}
								<p class="text-md italic">Nėra pasirinkto personažo</p>
							{/if}
						</div>
						{#if player.assigned_character && player.assigned_character.image}
							<img
								src={player.assigned_character.image}
								alt={player.assigned_character.name}
								class="h-16 w-16 rounded-full object-cover"
							/>
						{/if}
					</div>
					<p class="text-md mt-2">Taškai: {player.points}</p>
					<p class="text-md mt-1">
						Spėjimai: {player.correctGuesses ?? 0}/{players.length - 1}
					</p>
					{#if player.guesses}
						{#if getMyGuess(player.guesses)}
							<p class="text-md mt-1">
								Tavo spėjimas:
								<span
									class={getMyGuess(player.guesses).is_correct ? 'text-green-500' : 'text-red-500'}
								>
									{getMyGuess(player.guesses).guessed_character_name}
								</span>
							</p>
						{:else}
							<p class="text-md mt-1">
								Tavo spėjimas:
								<span class="text-red-500"> Neatlikai spėjimo šiam žaidėjui </span>
							</p>
						{/if}
					{/if}
				</div>
			{/each}
		</div>
	{/if}

	<button class="btn preset-filled-primary-500 mt-4" on:click={handleLeaveLobby}>
		Noriu žaisti vėl!
	</button>
</main>
