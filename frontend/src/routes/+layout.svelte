<!-- +layout.svelte -->
<script>
	import '../app.css';
	import { SvelteToast } from '@zerodevx/svelte-toast';
	import { browser } from '$app/environment';
	import Banner from '$lib/Banner.svelte';

	const options = {};
</script>

{#if browser}
	<SvelteToast {options} />
{/if}
<div class="flex h-full w-full flex-col items-center justify-center bg-[#464646]">
	<Banner />
	<main class="flex h-full flex-col items-center justify-center">
		<slot />
	</main>
</div>
