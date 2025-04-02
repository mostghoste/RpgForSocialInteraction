<!-- src/lib/Banner.svelte -->
<script>
	import { bannerData } from '$lib/stores';
	$: banner = $bannerData;
</script>

<header class="z-10 flex w-full flex-col items-center bg-[#8B3399] p-2 text-white">
	{#if banner.status === 'join_create'}
		<h1 class="text-2xl font-bold">Role playing game for social interaction</h1>
	{:else if banner.status === 'pending'}
		<h2 class="text-xl font-semibold">Kambario kodas: {banner.code}</h2>
	{:else if banner.status === 'in_progress'}
		{#if !banner.hasSentMessage}
			<p class="text-2xl">{banner.timeLeftFormatted}</p>
			<h2 class="text-3xl font-extrabold">ATSAKYK</h2>
			<h3 class="text-2xl font-semibold">{banner.question}</h3>
			<div class="mt-2 text-sm">
				<h4>Tu esi:</h4>
				<div class="flex items-center gap-1">
					{#if banner.characterImage}
						<div class="h-6 w-6 overflow-hidden rounded-full bg-[#DBA4EF]">
							<img src={banner.characterImage} alt="Avatar" />
						</div>
					{/if}
					<p class="text-base font-semibold">{banner.characterName}</p>
				</div>
			</div>
		{:else}
			<p class="text-xl">Kitam raundui liko: {banner.timeLeftFormatted}</p>
		{/if}
	{:else if banner.status === 'guessing'}
		<p class="text-2xl">Spėjimams liko: {banner.timeLeftFormatted}</p>
		<h2 class="text-3xl font-extrabold">Atspėk!</h2>
		<p class="mt-2">{banner.guessesSubmitted}/{banner.guessesNeeded} spėjimų pateikta</p>
	{:else if banner.status === 'completed'}
		<h2 class="text-xl font-semibold">Žaidimas baigtas!</h2>
	{/if}
</header>
