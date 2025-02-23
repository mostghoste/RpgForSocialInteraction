<script>
	import '../app.css';
	let { children } = $props();
</script>

<div class="h-full w-full bg-[#464646] px-2 py-4">
	{@render children()}
</div>
