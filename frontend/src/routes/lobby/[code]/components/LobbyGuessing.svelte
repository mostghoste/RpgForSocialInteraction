<!-- LobbyGuessing.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';

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
	<h2 class="h4">Spėjimų fazė</h2>
	<p>Liko laiko spėjimams</p>
	<h3>{guessTimeLeft}s</h3>
</Banner>

<main class="flex h-full w-full flex-col items-center justify-center gap-4 overflow-y-scroll">
	<div class="flex flex-col gap-4 md:flex-row">
		<!-- Players Column -->
		<div class="flex flex-1 flex-col">
			<h3 class="h3 mb-2 text-xl">Žaidėjai</h3>
			{#each players as player (player.id)}
				{#if String(player.id) !== String(participantId)}
					<button
						class="player-card mb-2 cursor-pointer rounded border p-2 {activePlayer === player.id
							? 'bg-surface-700-300 text-surface-contrast-700-300 scale-105 transition-all'
							: ''}"
						on:click={() => selectPlayer(player.id)}
					>
						<p><strong>{player.username}</strong></p>
						{#if guessMap[player.id]}
							<p class="text-sm">
								Spėjimas:
								{#each guessOptions.filter((opt) => opt.character_id === guessMap[player.id]) as guess}
									<span>{guess.character_name}</span>
								{/each}
							</p>
						{/if}
					</button>
				{/if}
			{/each}
		</div>

		<!-- Characters Column -->
		<div class="flex-1">
			<h3 class="mb-2 text-xl font-bold">Personažai</h3>
			<div class="grid grid-cols-2 gap-4 md:grid-cols-3">
				{#each guessOptions as character (character.character_id)}
					<div
						class="character-card cursor-pointer rounded border p-2 hover:shadow-lg {activeCharacter &&
						activeCharacter.character_id === character.character_id
							? 'bg-blue-100'
							: ''}"
						on:click={() => selectCharacter(character)}
					>
						<!-- Replace with an actual image if available -->
						<img
							src={character.image || '/fallback_character.jpg'}
							alt={character.character_name}
							class="h-16 w-full object-cover"
						/>
						<p class="mt-1 text-center text-sm">{character.character_name}</p>
					</div>
				{/each}
			</div>
		</div>
	</div>
</main>

<style>
	.character-card:hover {
		transform: translateY(-2px);
		transition: transform 0.1s ease-in-out;
	}
</style>
