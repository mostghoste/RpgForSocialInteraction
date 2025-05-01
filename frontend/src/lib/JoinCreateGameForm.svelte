<script>
	import { goto } from '$app/navigation';
	import { toast } from '@zerodevx/svelte-toast';
	import { toastOptions } from '$lib/toastConfig';
	import Banner from '$lib/Banner.svelte';
	import { user, clearTokens } from '$lib/stores/auth';
	import { User } from '@lucide/svelte';
	import { apiFetch } from '$lib/api';

	let code = '';
	let loading = false;
	let showMenu = false;

	async function createRoom() {
		loading = true;
		try {
			const res = await apiFetch('/api/create_room/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.error ?? 'Nepavyko sukurti kambario.', toastOptions.error);
			} else {
				const { code } = await res.json();
				goto(`/lobby/${code}`);
			}
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		} finally {
			loading = false;
		}
	}

	async function joinRoom() {
		if (!code) {
			toast.push('Įveskite kambario kodą!', toastOptions.error);
			return;
		}
		loading = true;
		try {
			const res = await apiFetch(`/api/verify_room/?code=${encodeURIComponent(code)}`, {
				method: 'GET'
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.error ?? 'Nepavyko rasti kambario.', toastOptions.error);
			} else {
				const { code: validCode } = await res.json();
				goto(`/lobby/${validCode}`);
			}
		} catch (e) {
			console.error(e);
			toast.push('Serverio klaida.', toastOptions.error);
		} finally {
			loading = false;
		}
	}

	function logout() {
		clearTokens();
		toast.push('Atsijungta.', toastOptions.success);
	}

	function handleClickOutside(e) {
		if (!e.target.closest('.user-menu-container')) showMenu = false;
	}
</script>

<svelte:window on:click={handleClickOutside} />

<Banner>
	<div class="relative flex w-full items-center justify-between">
		<span class="w-20 lg:w-32"></span>
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
						class="bg-surface-100-900 absolute right-0 z-10 mt-2 w-48 flex-col gap-2 rounded-lg p-3 shadow-lg"
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
		class="bg-surface-100-900 mx-auto flex w-fit flex-col items-center gap-4 rounded-2xl p-4 lg:max-w-3xl"
	>
		<div class="flex flex-col gap-2">
			<h1 class="h2">Sveikas atvykęs!</h1>
			<p>Įvesk kambario kodą arba sukurk naują kambarį.</p>
		</div>
		<div class="flex w-96 flex-col gap-2">
			<input
				class="input text-center"
				type="text"
				bind:value={code}
				maxlength="6"
				on:input={(e) => {
					code = e.target.value
						.replace(/[^A-Za-z]/g, '')
						.toUpperCase()
						.slice(0, 6);
				}}
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
	</section>
</main>
