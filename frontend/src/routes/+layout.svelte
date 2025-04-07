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
<div class="bg-surface-300-700 flex h-full w-full flex-col items-center justify-center">
	<!-- <main class="flex h-full flex-col items-center justify-center">

	</main> -->
	<slot />
</div>
