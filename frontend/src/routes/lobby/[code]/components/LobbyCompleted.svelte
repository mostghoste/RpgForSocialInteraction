<!-- src/routes/lobby/[code]/components/LobbyCompleted.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';

	// Expect the "players" array to have extra fields:
	// - assigned_character (object with at least a 'name' property)
	// - correctGuesses (number)
	// - myGuessCorrect (boolean) that is true if the current user guessed this player's character correctly.
	export let players = [];
	// You can also pass the current user's id if needed.
	export let currentUserId;

	const dispatch = createEventDispatcher();

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}
</script>

<Banner>
	<h2 class="h3">Žaidimas baigėsi!</h2>
</Banner>

<main class="flex h-full w-full flex-col items-center justify-center gap-4 overflow-y-scroll">
	<h3 class="h1">Rezultatai:</h3>
	<div class="grid w-full max-w-xl gap-4">
		{#each players as player}
			<div
				class="rounded-lg border p-4 shadow
				{player.myGuessCorrect ? 'border-green-500' : 'border-gray-300'}"
			>
				<div class="flex items-center justify-between">
					<div class="flex flex-col">
						<h4 class="text-xl font-bold">{player.username}{player.is_host ? ' 👑' : ''}</h4>
						{#if player.assigned_character}
							<p class="text-md">Personažas: {player.assigned_character.name}</p>
						{:else}
							<p class="text-md italic">Nėra pasirinkto personažo</p>
						{/if}
					</div>
					<!-- Optionally, show the character image if available -->
					{#if player.assigned_character && player.assigned_character.image}
						<img
							src={player.assigned_character.image}
							alt={player.assigned_character.name}
							class="h-16 w-16 rounded-full object-cover"
						/>
					{/if}
				</div>
				<p class="text-md mt-2">Taškai: {player.points}</p>
				<p class="text-md mt-1">Spėjimai: {player.correctGuesses ?? 0}/{players.length - 1}</p>
			</div>
		{/each}
	</div>
	<button class="btn preset-filled-primary-500 mt-4" on:click={handleLeaveLobby}>
		Noriu žaisti vėl!
	</button>
</main>
