<!-- +layout.svelte -->
<script>
	import '../app.css';
	import { SvelteToast } from '@zerodevx/svelte-toast';
	import { browser } from '$app/environment';

	const options = {};
</script>

{#if browser}
	<SvelteToast {options} />
{/if}
<svelte:head>
	<title>Meidvainis</title>
</svelte:head>

<div class="bg-surface-300-700 flex h-screen w-screen flex-col">
	<slot />
</div>
