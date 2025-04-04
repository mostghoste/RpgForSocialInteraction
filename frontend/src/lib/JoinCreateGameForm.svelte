<!-- src/lib/JoinCreateGameForm.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { toast } from '@zerodevx/svelte-toast';
	import { toastOptions } from '$lib/toastConfig';
	import Banner from '$lib/Banner.svelte';
	const API_URL = import.meta.env.VITE_API_BASE_URL;

	let code = '';
	let loading = false;

	async function createRoom() {
		loading = true;
		try {
			const response = await fetch(`${API_URL}/api/create_room/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});
			if (!response.ok) {
				const data = await response.json().catch(() => ({}));
				toast.push(data.error ?? 'Serverio klaida: Nepavyko sukurti kambario.', toastOptions.error);
				return;
			}
			const data = await response.json();
			goto(`/lobby/${data.code}`);
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida bandant sukurti kambarį.', toastOptions.error);
		} finally {
			loading = false;
		}
	}

	async function joinRoom() {
		if (!code) {
			toast.push('Prašome įrašyti kambario kodą!', toastOptions.error);
			return;
		}
		loading = true;
		try {
			const response = await fetch(`${API_URL}/api/verify_room/?code=${encodeURIComponent(code)}`, {
				method: 'GET'
			});
			if (!response.ok) {
				const data = await response.json().catch(() => ({}));
				toast.push(data.error ?? 'Nepavyko prisijungti.', toastOptions.error);
				return;
			}
			const data = await response.json();
			goto(`/lobby/${data.code}`);
		} catch (err) {
			console.error(err);
			toast.push('Serverio klaida bandant prisijungti prie kambario.', toastOptions.error);
		} finally {
			loading = false;
		}
	}
</script>

<Banner>
	<h1 class="text-2xl font-bold">Role playing game for social interaction</h1>
</Banner>
<main class="flex h-full flex-col items-center justify-center">
	<div>
		<input class="border" type="text" bind:value={code} placeholder="Įveskite kambario kodą" />
		<button class="border" on:click={createRoom} disabled={loading}>Sukurti kambarį</button>
		<button class="border" on:click={joinRoom} disabled={!code || loading}>Prisijungti</button>
	</div>
</main>
