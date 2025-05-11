<!-- src/routes/login/+page.svelte -->
<script>
	import { setTokens } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { toast } from '@zerodevx/svelte-toast';
	import { toastOptions } from '$lib/toastConfig';
	const API_URL = import.meta.env.VITE_API_BASE_URL;

	let activeTab = 'login';

	let username = '';
	let password = '';
	let email = '';

	const usernameRe = /^[A-Za-z0-9@.+\-_]{4,30}$/;
	const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

	$: validUsername = usernameRe.test(username);
	$: validPassword = password.length >= 8;
	$: validEmail = activeTab === 'register' ? emailRe.test(email) : true;
	$: canSubmit =
		activeTab === 'login'
			? validUsername && validPassword
			: validUsername && validPassword && validEmail;

	async function login() {
		if (!canSubmit) return;
		try {
			const res = await fetch(`${API_URL}/api/token/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username, password })
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				toast.push(err.detail ?? 'Neteisingi prisijungimo duomenys', toastOptions.error);
				return;
			}
			const data = await res.json();
			setTokens(data);
			toast.push('Sėkmingai prisijungta!', toastOptions.success);
			goto('/');
		} catch {
			toast.push('Serverio klaida prisijungiant', toastOptions.error);
		}
	}

	async function register() {
		if (!canSubmit) return;
		try {
			const res = await fetch(`${API_URL}/api/register/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username, password, email })
			});
			if (!res.ok) {
				const data = await res.json().catch(() => ({}));
				const msg =
					data.username?.[0] || data.password?.[0] || data.email?.[0] || 'Nepavyko registruotis';
				toast.push(msg, toastOptions.error);
				return;
			}
			toast.push('Sėkmingai užsiregistruota!', toastOptions.success);
			await login();
		} catch {
			toast.push('Serverio klaida registruojantis', toastOptions.error);
		}
	}
</script>

<div class="flex h-full items-center">
	<section
		class="bg-surface-100-900 mx-auto flex w-fit flex-col items-center gap-4 rounded-2xl p-4 lg:max-w-3xl"
	>
		<div class="flex w-full gap-4">
			<button
				class="text-md border-b-2 pb-2 focus:outline-none"
				class:border-primary-500={activeTab === 'login'}
				class:border-transparent={activeTab !== 'login'}
				class:font-semibold={activeTab === 'login'}
				on:click={() => (activeTab = 'login')}
			>
				Prisijungti
			</button>
			<button
				class="text-md border-b-2 pb-2 focus:outline-none"
				class:border-primary-500={activeTab === 'register'}
				class:border-transparent={activeTab !== 'register'}
				class:font-semibold={activeTab === 'register'}
				on:click={() => (activeTab = 'register')}
			>
				Registruotis
			</button>
		</div>

		<form
			class="flex w-full flex-col gap-2"
			on:submit|preventDefault={() => (activeTab === 'login' ? login() : register())}
		>
			<input type="text" bind:value={username} placeholder="Naudotojo vardas" class="input" />
			{#if username && !validUsername}
				<p class="text-sm text-red-500">4–30 simbolių: raidės, skaičiai arba @ . + - _</p>
			{/if}

			<input type="password" bind:value={password} placeholder="Slaptažodis" class="input" />
			{#if password && !validPassword}
				<p class="text-sm text-red-500">Slaptažodis turi būti bent 8 simbolių ilgio</p>
			{/if}

			{#if activeTab === 'register'}
				<input type="email" bind:value={email} placeholder="El. paštas" class="input" />
				{#if email && !validEmail}
					<p class="text-sm text-red-500">Neteisingo formato el. paštas</p>
				{/if}
			{/if}

			<button
				type="submit"
				class="btn preset-filled-primary-400-600 mt-4 w-full"
				disabled={!canSubmit}
			>
				{activeTab === 'login' ? 'Prisijungti' : 'Registruotis'}
			</button>
		</form>
	</section>
</div>
