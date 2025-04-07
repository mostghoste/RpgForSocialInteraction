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
	<h1 class="h2 text-center">Role playing game for social interaction</h1>
</Banner>
<main class="flex h-full items-center justify-center p-2">
	<section
		class="bg-surface-100-900 flex w-full flex-col items-center gap-2 rounded-2xl p-4 lg:max-w-3xl"
	>
		<h1 class="h1">Sveikas atvykęs!</h1>
		<p class="text-center">
			Įvesk kambario kodą kad prisijungtum prie žaidimo, arba sukurk savo kambarį.
		</p>
		<div class="flex w-96 flex-col gap-1">
			<input class="input text-center" type="text" bind:value={code} placeholder="Kambario kodas" />
			<footer class="flex gap-1">
				<button
					class="btn preset-filled-primary-400-600 w-1/2"
					on:click={createRoom}
					disabled={loading}>Sukurti kambarį</button
				>
				<button
					class="btn preset-filled-success-50-950 w-full"
					on:click={joinRoom}
					disabled={!code || loading}>Prisijungti</button
				>
			</footer>
		</div>
	</section>
</main>
