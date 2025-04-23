<!-- src/routes/login/+page.svelte -->
<script>
	import { setTokens, clearTokens } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { toast } from '@zerodevx/svelte-toast';
	import { toastOptions } from '$lib/toastConfig';
	const API_URL = import.meta.env.VITE_API_BASE_URL;

	let activeTab = 'login';

	// form fields
	let username = '';
	let password = '';
	let email = '';
	let error = '';

	async function login() {
		error = '';
		try {
			const res = await fetch(`${API_URL}/api/token/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username, password })
			});
			if (!res.ok) {
				error = 'Neteisingi prisijungimo duomenys';
				return;
			}
			const data = await res.json();
			setTokens(data);
			goto('/');
		} catch {
			error = 'Serverio klaida prisijungiant';
		}
	}

	async function register() {
		error = '';
		try {
			const res = await fetch(`${API_URL}/api/register/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username, password /* , email */ })
			});
			if (!res.ok) {
				const data = await res.json().catch(() => ({}));
				error = data.username?.[0] || data.password?.[0] || 'Nepavyko registruotis';
				return;
			}
			await login();
		} catch {
			error = 'Serverio klaida registruojantis';
		}
	}
</script>

<div class="bg-surface-100-900 mx-auto mt-10 max-w-md rounded p-6 shadow">
	<div class="tabs">
		<button
			class="tab {activeTab === 'login' ? 'active' : ''}"
			on:click={() => (activeTab = 'login')}
		>
			Prisijungti
		</button>
		<button
			class="tab {activeTab === 'register' ? 'active' : ''}"
			on:click={() => (activeTab = 'register')}
		>
			Registruotis
		</button>
	</div>

	{#if activeTab === 'login'}
		<h2 class="mb-4 text-2xl">Prisijungimas</h2>
	{:else}
		<h2 class="mb-4 text-2xl">Registracija</h2>
	{/if}

	{#if error}
		<p class="mb-2 text-red-500">{error}</p>
	{/if}

	<div class="flex flex-col gap-4">
		<input
			type="text"
			placeholder="Vartotojo vardas"
			bind:value={username}
			class="rounded border p-2"
		/>
		<input
			type="password"
			placeholder="Slaptažodis"
			bind:value={password}
			class="rounded border p-2"
		/>

		{#if activeTab === 'register'}
			<!-- optional extra fields, e.g. email -->
			<!--
		<input
		  type="email"
		  placeholder="El. paštas"
		  bind:value={email}
		  class="border p-2 rounded"
		/>
		-->
		{/if}

		<button
			class="btn preset-filled-primary-400-600 mt-2"
			on:click={activeTab === 'login' ? login : register}
		>
			{activeTab === 'login' ? 'Prisijungti' : 'Registruotis'}
		</button>
	</div>
</div>

<style>
	.tabs {
		display: flex;
		gap: 1rem;
		margin-bottom: 1rem;
	}
	.tab {
		padding: 0.5rem 1rem;
		cursor: pointer;
		border-bottom: 2px solid transparent;
	}
	.tab.active {
		border-color: var(--color-primary-500);
		font-weight: bold;
	}
</style>
