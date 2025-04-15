<!-- src/routes/lobby/[code]/components/LobbyCompleted.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';

	export let players = [];

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
	<ul>
		{#each players as player}
			<li>{player.username}: {player.points} taškai</li>
		{/each}
	</ul>
	<button class="btn preset-filled-primary-500" on:click={handleLeaveLobby}
		>Noriu žaisti vėl!</button
	>
</main>
