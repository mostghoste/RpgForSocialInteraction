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
	<h2>Žaidimas baigtas!</h2>
</Banner>

<div class="completed-view">
	<h3>Rezultatai:</h3>
	<ul>
		{#each players as player}
			<li>{player.username}: {player.points} taškai</li>
		{/each}
	</ul>
	<button class="border" on:click={handleLeaveLobby}>Išeiti</button>
</div>
