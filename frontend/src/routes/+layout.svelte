<script>
	import '../app.css';
	import avatar from '$lib/avatar.png';
	let { children } = $props();
</script>

<div class="h-full w-full bg-[#464646] px-2 py-4">
	{@render children()}
</div>
<!-- Notification -->
<!-- <section
	class="absolute top-0 flex h-fit w-full flex-col items-center bg-[#8B3399] p-2 text-center text-white"
>
	<p class="text-[32px]">1 min 03 s</p>
	<h2 class="text-[40px] font-extrabold">ATSAKYK</h2>
	<h3 class=" text-[32px] font-semibold">Kuris lietuviškas patiekalas geriausias?</h3>
	<div>
		<h4 class=" text-[14px]">Tu esi:</h4>
		<div class="flex gap-1">
			<div class="h-6 w-6 rounded-full bg-[#DBA4EF]">
				<img src={avatar} alt="Player avatar" />
			</div>
			<p class="text-[16px] font-semibold">Karalius Lodorius IV</p>
		</div>
	</div>
</section> -->
