<!-- src/routes/lobby/[code]/components/LobbyGuessing.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	export let guessTimeLeft;
	export let players;
	export let participantId;
	export let guessOptions;
	export let guessMap; // e.g. { [playerId]: characterId }

	const dispatch = createEventDispatcher();

	function handleChangeGuess(playerId, charId) {
		guessMap[playerId] = charId;
	}

	function handleSubmitGuesses() {
		dispatch('submitGuesses');
	}

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}
</script>

<div class="guessing-view">
	<h2>Atspėk draugus! 👀</h2>
	<p>Liko laiko spėjimams: {guessTimeLeft}s</p>
	<p>Pasirink, kurį personažą, manai, žaidžia kiekvienas iš kitų žaidėjų.</p>

	<div class="guessing-panel">
		{#each players as player}
			{#if String(player.id) !== String(participantId)}
				<div class="guessing-card">
					<p><strong>{player.username}</strong></p>
					<select
						bind:value={guessMap[player.id]}
						on:change={(e) => handleChangeGuess(player.id, e.target.value)}
					>
						<option value="" disabled selected>Pasirink personažą</option>
						{#each guessOptions as option}
							<option value={option.character_id}>{option.character_name}</option>
						{/each}
					</select>
				</div>
			{/if}
		{/each}
	</div>

	<button class="border" on:click={handleSubmitGuesses} disabled={guessTimeLeft === 0}>
		Pateikti spėjimus
	</button>

	<button class="border" on:click={handleLeaveLobby}>Palikti kambarį</button>
</div>
