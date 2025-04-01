<script>
	import { createEventDispatcher } from 'svelte';

	export let players = [];

	const dispatch = createEventDispatcher();

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}
</script>

<div class="completed-view">
	<h2>Žaidimas baigtas!</h2>
	<h3>Rezultatai:</h3>
	<ul>
		{#each players as player}
			<li>{player.username}: {player.points} taškai</li>
		{/each}
	</ul>
	<button class="border" on:click={handleLeaveLobby}>Išeiti</button>
</div>
