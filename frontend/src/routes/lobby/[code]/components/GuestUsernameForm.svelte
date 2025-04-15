<!-- src/routes/lobby/[code]/components/GuestUsernameForm.svelte -->
<script>
	import { createEventDispatcher, onMount } from 'svelte';
	import Banner from '$lib/Banner.svelte';
	const dispatch = createEventDispatcher();

	export let code;
	let guestUsername = '';
	let usernameInput;
	// On component mount, focus the input field
	onMount(() => {
		usernameInput && usernameInput.focus();
	});

	function handleSubmit() {
		dispatch('submitGuestUsername', { guestUsername });
	}
</script>

<Banner>
	<h2 class="h3 text-center">Kambario {code} laukiamasis</h2>
</Banner>

<main class="flex h-full flex-col items-center justify-center">
	<section class="bg-surface-100-900 flex flex-col gap-4 rounded-2xl p-4">
		<div class="flex flex-col gap-2">
			<h1 class="h3">Kas tu?</h1>
			<p class="text-center">Įvesk savo vardą, kad prisijungtum prie kambario.</p>
		</div>
		<div class="flex flex-col gap-2">
			<input
				class="input text-center"
				type="text"
				bind:value={guestUsername}
				placeholder="Vartotojo vardas"
				bind:this={usernameInput}
				on:keydown={(e) => {
					if (
						e.key === 'Enter' &&
						guestUsername.trim().length >= 3 &&
						guestUsername.trim().length <= 20
					) {
						handleSubmit();
					}
				}}
			/>
			<button
				class="btn preset-filled-primary-500"
				on:click={handleSubmit}
				disabled={guestUsername.trim().length < 3 || guestUsername.trim().length > 20}
			>
				Prisijungti
			</button>
		</div>
	</section>
</main>
