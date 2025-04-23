<!-- src/lib/JoinCreateGameForm.svelte -->
<script>
	import { goto } from '$app/navigation';
	import { toast } from '@zerodevx/svelte-toast';
	import { toastOptions } from '$lib/toastConfig';
	import Banner from '$lib/Banner.svelte';
	import { user, clearTokens } from '$lib/stores/auth';
	import { User } from '@lucide/svelte';

	const API_URL = import.meta.env.VITE_API_BASE_URL;

	let code = '';
	let loading = false;
	let showMenu = false;

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

	function logout() {
		clearTokens();
		toast.push('Atsijungta', toastOptions.success);
		goto('/login');
	}

	// close menu when clicking outside
	function handleClickOutside(event) {
		if (!event.target.closest('.user-menu-container')) {
			showMenu = false;
		}
	}
</script>

<svelte:window on:click={handleClickOutside} />

<Banner>
	<div class="relative flex w-full items-center justify-between">
		<span class="sm:w-16 md:w-48"></span>
		<h1 class="h3 text-center">Role playing game for social interaction</h1>

		{#if $user}
			<div class="user-menu-container">
				<button
					class="btn preset-filled-primary-500 flex items-center gap-1 text-sm"
					on:click={() => (showMenu = !showMenu)}
				>
					<User size={20} />
					<span class="hidden lg:block">{$user.username}</span>
				</button>

				{#if showMenu}
					<div
						class="bg-surface-100-900 absolute right-0 z-10 mt-2 flex w-48 flex-col gap-2 rounded-lg p-3 shadow-lg"
					>
						<p class="text-center text-sm">Sveikas, <strong>{$user.username}</strong>!</p>
						<hr />
						<button class="btn preset-filled-error-400-600 text-sm" on:click={logout}>
							Atsijungti
						</button>
					</div>
				{/if}
			</div>
		{:else}
			<button class="btn preset-filled-primary-400-600" on:click={() => goto('/login')}>
				Prisijungti
			</button>
		{/if}
	</div>
</Banner>

<main class="flex h-full items-center justify-center p-2">
	<section
		class="bg-surface-100-900 flex w-fit flex-col items-center gap-4 rounded-2xl p-4 lg:max-w-3xl"
	>
		<div class="flex flex-col gap-2">
			<h1 class="h2">Sveikas atvykęs!</h1>
			<p>Įvesk kambario kodą kad prisijungtum prie žaidimo, arba sukurk savo kambarį.</p>
		</div>
		<div>
			<div class="flex w-96 flex-col gap-2">
				<input
					class="input text-center"
					type="text"
					bind:value={code}
					placeholder="Kambario kodas"
				/>
				<footer class="flex gap-2">
					<button
						class="btn preset-filled-primary-400-600 w-1/2"
						on:click={createRoom}
						disabled={loading}
					>
						Sukurti kambarį
					</button>
					<button
						class="btn preset-filled-success-50-950 w-full"
						on:click={joinRoom}
						disabled={!code || loading}
					>
						Prisijungti
					</button>
				</footer>
			</div>
		</div>
	</section>
</main>
