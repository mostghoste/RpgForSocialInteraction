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
	<h2>Kambario {code} laukiamasis</h2>
</Banner>

<main class="flex h-full flex-col items-center justify-center gap-2">
	<h1 class="h1">Kas tu?</h1>
	<p>Įvesk savo vartotojo vardą, kad prisijungtum prie kambario.</p>
	<div class="flex flex-col gap-1">
		<input
			class="input text-center"
			type="text"
			bind:value={guestUsername}
			placeholder="Vartotojo vardas"
		/>
		<button
			class="btn preset-filled-primary-500"
			on:click={handleSubmit}
			disabled={guestUsername.trim().length < 3 || guestUsername.trim().length > 20}
		>
			Prisijungti
		</button>
	</div>
</main>
