<!-- src/routes/lobby/[code]/components/GuestUsernameForm.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';
	const dispatch = createEventDispatcher();

	export let code;
	let guestUsername = '';

	function handleSubmit() {
		dispatch('submitGuestUsername', { guestUsername });
	}
</script>

<Banner>
	<h2>Kambario kodas: {code}</h2>
</Banner>

<main class="flex h-full flex-col items-center justify-center">
	<h1 class="text-2xl font-semibold">Kas tu?</h1>
	<p class="text-white">Įvesk savo vartotojo vardą, kad prisijungtum prie kambario.</p>
	<input class="border" type="text" bind:value={guestUsername} placeholder="Vartotojo vardas" />
	<button class="border" on:click={handleSubmit}>Prisijungti</button>
</main>
