<!-- +layout.svelte -->
<script>
	import '../app.css';
	import { SvelteToast } from '@zerodevx/svelte-toast';
	import { browser } from '$app/environment';
	import { gameBannerStore } from '$lib/stores.js';

	const options = {};

	$: bannerData = $gameBannerStore;
</script>

<!-- Banner / notification bar -->
<header class="fixed w-full text-center text-white" style="z-index: 1000;">
	{#if bannerData.status === 'join_create'}
		<section class="bg-[#8B3399] p-2">
			<h1 class="text-2xl font-bold">Role playing game for social interaction</h1>
		</section>
	{:else if bannerData.status === 'pending'}
		<section class="bg-[#8B3399] p-2">
			<h2 class="text-xl font-semibold">Kambario kodas: {bannerData.code}</h2>
		</section>
	{:else if bannerData.status === 'in_progress'}
		{#if !bannerData.hasSentMessage}
			<!-- Large banner -->
			<section class="flex flex-col items-center bg-[#8B3399] p-2">
				<p class="text-2xl">{bannerData.timeLeftFormatted}</p>
				<h2 class="text-3xl font-extrabold">ATSAKYK</h2>
				<h3 class="text-2xl font-semibold">{bannerData.question}</h3>
				<div class="mt-2 text-sm">
					<h4>Tu esi:</h4>
					<div class="flex items-center gap-1">
						<!-- If we have a character image, display it -->
						{#if bannerData.characterImage}
							<div class="h-6 w-6 overflow-hidden rounded-full bg-[#DBA4EF]">
								<img src={bannerData.characterImage} alt="Avatar" />
							</div>
						{/if}
						<p class="text-base font-semibold">{bannerData.characterName}</p>
					</div>
				</div>
			</section>
		{:else}
			<!-- Small banner, e.g. green background once user has answered -->
			<section class="bg-green-700 p-2">
				<p class="text-xl">
					Kitam raundui liko: {bannerData.timeLeftFormatted}
				</p>
			</section>
		{/if}
	{:else if bannerData.status === 'guessing'}
		<!-- 4) Guessing: show big banner with time left, guesses made/needed -->
		<section class="bg-[#8B3399] p-2">
			<p class="text-2xl">Spėjimams liko: {bannerData.timeLeftFormatted}</p>
			<h2 class="text-3xl font-extrabold">Atspėk!</h2>
			<p class="mt-2">
				{bannerData.guessesSubmitted}/{bannerData.guessesNeeded} spėjimų pateikta
			</p>
		</section>
	{:else if bannerData.status === 'completed'}
		<!-- If you want a banner in the completed state, do so here. -->
		<section class="bg-[#8B3399] p-2">
			<h2 class="text-xl font-semibold">Žaidimas baigtas!</h2>
		</section>
	{/if}
</header>

<div class="flex h-full w-full flex-col items-center justify-center bg-[#464646] px-2 py-4 pt-24">
	<slot />
	{#if browser}
		<SvelteToast {options} />
	{/if}
</div>
