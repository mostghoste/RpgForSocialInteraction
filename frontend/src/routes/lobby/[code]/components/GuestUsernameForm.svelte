<!-- /lobby/[code]/components/GuestUsernameForm.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	export let code;
	export let errorMessage;
	const dispatch = createEventDispatcher();

	let guestUsername = '';

	function handleSubmit() {
		// We dispatch an event named "submitGuestUsername"
		// and include the username in event.detail
		dispatch('submitGuestUsername', { guestUsername });
	}
</script>

<h2>Kambario kodas: {code}</h2>
<p>Prašome įvesti vartotojo vardą, kad prisijungtumėte prie kambario.</p>
<input class="border" type="text" bind:value={guestUsername} placeholder="Vartotojo vardas" />
<button class="border" on:click={handleSubmit}>Prisijungti</button>

{#if errorMessage}
	<p class="error">{errorMessage}</p>
{/if}
