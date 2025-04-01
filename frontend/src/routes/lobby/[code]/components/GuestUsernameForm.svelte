<!-- src/routes/lobby/[code]/components/GuestUsernameForm.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();

	export let code;

	let guestUsername = '';

	function handleSubmit() {
		dispatch('submitGuestUsername', { guestUsername });
	}
</script>

<h2>Kambario kodas: {code}</h2>
<p>Prašome įvesti vartotojo vardą, kad prisijungtumėte prie kambario.</p>
<input class="border" type="text" bind:value={guestUsername} placeholder="Vartotojo vardas" />
<button class="border" on:click={handleSubmit}>Prisijungti</button>
