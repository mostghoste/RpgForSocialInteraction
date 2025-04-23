<script>
	import { setTokens } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	let username = '',
		password = '',
		error = '';

	async function login() {
		const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/token/`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ username, password })
		});
		if (!res.ok) {
			error = 'Invalid credentials';
			return;
		}
		const data = await res.json();
		setTokens(data);
		goto('/');
	}

	import { clearTokens } from '$lib/stores/auth';
	async function logout() {
		// blacklist the refresh token on server
		await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/logout/`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ refresh: localStorage.getItem('refresh') })
		});
		clearTokens();
		location.href = '/login';
	}
</script>

<input bind:value={username} placeholder="Username" />
<input type="password" bind:value={password} placeholder="Password" />
<button on:click={login}>Log In</button>
{#if error}<p class="error">{error}</p>{/if}

<button on:click={logout}>Log Out</button>
