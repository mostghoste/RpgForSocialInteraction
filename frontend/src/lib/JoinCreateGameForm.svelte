<!-- JoinCreateGameForm.svelte -->

<script>
	import { goto } from '$app/navigation';
	const API_URL = import.meta.env.VITE_API_BASE_URL;
	let code = '';
	let errorMessage = '';
	let loading = false;

	async function createRoom() {
		errorMessage = '';
		loading = true;
		try {
			const response = await fetch(`${API_URL}/api/create_room/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});
			if (!response.ok) {
				const data = await response.json().catch(() => ({}));
				errorMessage = data.error ?? 'Serverio klaida: Nepavyko sukurti kambario.';
				return;
			}
			const data = await response.json();
			// Navigate to the lobby page with the returned code
			goto(`/lobby/${data.code}`);
		} catch (err) {
			console.error(err);
			errorMessage = 'Serverio klaida bandant sukurti kambarį.';
		} finally {
			loading = false;
		}
	}

	async function joinRoom() {
		if (!code) {
			errorMessage = 'Prašome įrašyti kambario kodą!';
			return;
		}
		errorMessage = '';
		loading = true;
		try {
			// Call the verify_room GET endpoint with the room code as a query parameter.
			const response = await fetch(`${API_URL}/api/verify_room/?code=${encodeURIComponent(code)}`, {
				method: 'GET'
			});
			if (!response.ok) {
				const data = await response.json().catch(() => ({}));
				errorMessage = data.error ?? 'Nepavyko prisijungti.';
				return;
			}
			const data = await response.json();
			// If verification is successful, redirect to the lobby page.
			goto(`/lobby/${data.code}`);
		} catch (err) {
			console.error(err);
			errorMessage = 'Serverio klaida bandant prisijungti prie kambario.';
		} finally {
			loading = false;
		}
	}
</script>

<div>
	<input class="border" type="text" bind:value={code} placeholder="Įveskite kambario kodą" />
	<button class="border" on:click={createRoom} disabled={loading}>Sukurti kambarį</button>
	<button class="border" on:click={joinRoom} disabled={!code || loading}>Prisijungti</button>

	{#if errorMessage}
		<p class="error">{errorMessage}</p>
	{/if}
</div>
