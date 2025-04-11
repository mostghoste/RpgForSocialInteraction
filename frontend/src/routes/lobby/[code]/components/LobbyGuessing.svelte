<!-- LobbyGuessing.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';

	export let guessTimeLeft;
	export let players;
	export let participantId;
	export let guessOptions;

	export let guessMap = {}; // { [playerId]: characterId }

	const dispatch = createEventDispatcher();

	// Store the currently selected player for assigning a guess
	let activePlayer = null;

	function selectPlayer(playerId) {
		activePlayer = playerId;
	}

	function selectCharacter(character) {
		if (activePlayer) {
			guessMap[activePlayer] = character.character_id;
			activePlayer = null;
		} else {
			// Optionally, you can show a toast prompting the user to first choose a player.
			alert('Pirma pasirinkite žaidėją, kuriam norite priskirti spėjimą.');
		}
	}

	function handleSubmitGuesses() {
		dispatch('submitGuesses', { guessMap });
	}

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}
</script>

<Banner>
	<h2 class="h4">Spėjimų fazė</h2>
	<p>Liko laiko spėjimams</p>
	<h3>{guessTimeLeft}s</h3>
</Banner>

<main class="p-4">
	<div class="flex flex-col gap-4 md:flex-row">
		<!-- Players Column -->
		<div class="flex-1">
			<h3 class="mb-2 text-xl font-bold">Žaidėjai</h3>
			{#each players as player (player.id)}
				{#if String(player.id) !== String(participantId)}
					<div
						class="player-card mb-2 cursor-pointer rounded border p-2 {activePlayer === player.id
							? 'bg-blue-100'
							: ''}"
						on:click={() => selectPlayer(player.id)}
					>
						<p><strong>{player.username}</strong></p>
						{#if guessMap[player.id]}
							<p class="text-sm text-gray-600">
								Spėjimas:
								{#each guessOptions.filter((opt) => opt.character_id === guessMap[player.id]) as guess}
									<span>{guess.character_name}</span>
								{/each}
							</p>
						{/if}
					</div>
				{/if}
			{/each}
		</div>

		<!-- Characters Column -->
		<div class="flex-1">
			<h3 class="mb-2 text-xl font-bold">Personažai</h3>
			<div class="grid grid-cols-2 gap-4 md:grid-cols-3">
				{#each guessOptions as character (character.character_id)}
					<div
						class="character-card cursor-pointer rounded border p-2 hover:shadow-lg"
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

	<!-- Action Buttons -->
	<div class="mt-6 flex justify-center gap-4">
		<button class="btn preset-filled-success" on:click={handleSubmitGuesses}>
			Pateikti spėjimus
		</button>
		<button class="btn preset-filled-error" on:click={handleLeaveLobby}> Palikti kambarį </button>
	</div>
</main>

<style>
	.player-card:hover {
		background-color: #f0f0f0;
	}
	.character-card:hover {
		transform: translateY(-2px);
		transition: transform 0.1s ease-in-out;
	}
</style>
