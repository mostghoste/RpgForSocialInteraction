<!-- LobbyGuessing.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';
	import { Avatar } from '@skeletonlabs/skeleton-svelte';

	export let guessTimeLeft;
	export let players;
	export let participantId;
	export let guessOptions;

	// holds submitted guesses
	export let guessMap = {}; // { [playerId]: characterId }

	const dispatch = createEventDispatcher();

	// when both are chosen, a guess is automatically assigned and submitted.
	let activePlayer = null;
	let activeCharacter = null;

	function assignGuess() {
		if (activePlayer && activeCharacter) {
			// Record the guess
			guessMap[activePlayer] = activeCharacter.character_id;
			// Automatically submit this guess immediately.
			dispatch('submitGuesses', { guessMap });
			// Clear the active selections so that the user can make additional matches.
			activePlayer = null;
			activeCharacter = null;
		}
	}

	function selectPlayer(playerId) {
		activePlayer = playerId;
		assignGuess();
	}

	function selectCharacter(character) {
		activeCharacter = character;
		assignGuess();
	}

	// Leave lobby action remains as before.
	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}
</script>

<Banner>
	<h2 class="h4">Metas spėjimams!</h2>
	<p>Tau dar reikia atlikti 3 spėjimus</p>
	<h3>{guessTimeLeft}s</h3>
</Banner>

<main class="flex h-full w-full flex-col items-center justify-center gap-4 overflow-y-scroll">
	<div class="flex flex-col gap-4 md:flex-row">
		<!-- Players -->
		<div class="bg-surface-100-900 flex flex-1 flex-col gap-2 rounded-2xl p-4">
			<h3 class="h3 mb-2 text-xl">Žaidėjai</h3>
			{#each players as player (player.id)}
				{#if String(player.id) !== String(participantId)}
					<button
						class="bg-surface-200-800 border-primary-900-100 box-border h-16 rounded-xl p-2 transition-all hover:scale-105 {activePlayer ===
						player.id
							? 'scale-105 border'
							: ''}"
						on:click={() => selectPlayer(player.id)}
					>
						<p><strong>{player.username}</strong></p>
						{#if guessMap[player.id]}
							<p class="text-sm">
								{#each guessOptions.filter((opt) => opt.character_id === guessMap[player.id]) as guess}
									<span>{guess.character_name}</span>
								{/each}
							</p>
						{/if}
					</button>
				{/if}
			{/each}
		</div>

		<!-- Characters -->
		<div class="bg-surface-100-900 flex-1 gap-2 rounded-2xl p-4">
			<h3 class="mb-2 text-xl font-bold">Personažai</h3>
			<div class="grid grid-cols-2 gap-4 md:grid-cols-3">
				{#each guessOptions as character (character.character_id)}
					<button
						class="bg-surface-200-800 border-primary-900-100 box-border flex flex-col items-center justify-center rounded-xl p-2 transition-all hover:scale-105 {activeCharacter &&
						activeCharacter.character_id === character.character_id
							? 'scale-105 border'
							: ''}"
						on:click={() => selectCharacter(character)}
					>
						<Avatar
							src={character.image || '/fallback_character.jpg'}
							name={character.character_name}
						></Avatar>
						<p class="text-center font-semibold">{character.character_name}</p>
					</button>
				{/each}
			</div>
		</div>
	</div>
</main>
