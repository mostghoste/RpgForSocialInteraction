<script>
	import { onMount } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';

	// Expects "players" passed in with extra fields:
	// - is_npc: boolean
	// - assigned_character: { name, image? }
	// - correctGuesses: number
	// - guesses: an array of { guesser_id, guessed_character_name, is_correct }
	export let players = [];
	export let currentUserId;

	const dispatch = createEventDispatcher();

	// Only keep human players for podium + final
	$: humanPlayers = players.filter((p) => !p.is_npc);

	let revealedPlayers = [];
	let revealedPodium = [];

	let phase = 'identity'; // phases: 'identity', 'podium', 'final'
	const identityDelay = 3000;
	const podiumDelay = 3000;
	const podiumItemDelay = 3000;
	let podiumPlayers = [];

	// Gradually reveal **all** player identities (including NPCs)
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

	// Start the podium reveal (up to top 3 human players), always revealing lowest rank first
	function startPodiumReveal() {
		// sort descending and take top 3
		podiumPlayers = [...humanPlayers].sort((a, b) => b.points - a.points).slice(0, 3);

		// reverse so we reveal 3rd→1st (or 2nd→1st if only 2 players, or just 1st)
		const order = [...podiumPlayers].reverse();

		// switch phase immediately so your {#if phase==='podium'} block shows up
		phase = 'podium';

		order.forEach((player, index) => {
			setTimeout(
				() => {
					revealedPodium = [...revealedPodium, player];

					// once the last one is in, wait podiumItemDelay then go to final
					if (index === order.length - 1) {
						setTimeout(() => {
							phase = 'final';
						}, podiumItemDelay);
					}
				},
				podiumItemDelay * (index + 1)
			);
		});
	}

	// Helper to return the current user's guess from a list of guesses.
	function getMyGuess(guesses) {
		return guesses?.find((g) => g.guesser_id === currentUserId) ?? null;
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

<main class="flex h-full w-full flex-col items-center justify-center gap-4 overflow-y-auto p-4">
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
						{#if player.assigned_character?.image}
							<img
								src={player.assigned_character.image}
								alt={player.assigned_character.name}
								class="h-16 w-16 rounded-full object-cover"
							/>
						{/if}
					</div>
					<p class="text-md mt-2">
						{player.correctGuesses} iš {humanPlayers.length - 1} žaidėjų atspėjo!
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
							: `${i + 1}. vieta`}
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
			{#each humanPlayers as player (player.id)}
				<div
					class="rounded-lg border p-4 shadow {getMyGuess(player.guesses)?.is_correct
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
						{#if player.assigned_character?.image}
							<img
								src={player.assigned_character.image}
								alt={player.assigned_character.name}
								class="h-16 w-16 rounded-full object-cover"
							/>
						{/if}
					</div>
					<p class="text-md mt-2">Taškai: {player.points}</p>
					<p class="text-md mt-1">
						Spėjimai: {player.correctGuesses ?? 0}/{humanPlayers.length - 1}
					</p>
					{#if player.score_breakdown?.length}
						<details class="mt-2">
							<summary class="text-sm font-semibold">Detalių suskirstymas</summary>
							<ul class="ml-4 mt-1 list-disc text-sm">
								{#each player.score_breakdown as line}
									<li>{line.description} (<strong>+{line.points}</strong>)</li>
								{/each}
							</ul>
						</details>
					{/if}

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
		<button class="btn preset-filled-primary-500 mt-4" on:click={handleLeaveLobby}>
			Noriu žaisti vėl!
		</button>
	{/if}
</main>
