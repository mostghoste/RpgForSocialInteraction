<!-- frontend/src/lib/Banner.svelte -->
<script>
	export let variant = 'default'; // "default", "success"
	let bgClass = variant === 'success' ? 'bg-green-500' : 'bg-[#8B3399]';
</script>

<header
	class="flex w-full flex-col items-center {bgClass} selection:text-primary-700 relative p-2 text-2xl selection:bg-white/80"
>
	<slot />
</header>
