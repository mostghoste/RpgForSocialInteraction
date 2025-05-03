<script>
	import { onMount, tick, createEventDispatcher } from 'svelte';
	import { fly } from 'svelte/transition';
	import Banner from '$lib/Banner.svelte';
	import { Tooltip } from '@skeletonlabs/skeleton-svelte';

	// Expects "players" passed in with extra fields:
	// - is_npc: boolean
	// - assigned_character: { name, image? }
	// - correctGuesses: number
	// - guesses: an array of { guesser_id, guessed_character_name, is_correct }
	export let players = [];
	export let currentUserId;

	const dispatch = createEventDispatcher();

	$: humanPlayers = players.filter((p) => !p.is_npc);
	$: sortedHumanPlayers = [...humanPlayers].sort((a, b) => b.points - a.points);

	let revealedPlayers = [];
	let revealedPodium = [];

	let phase = 'identity'; // phases: 'identity', 'podium', 'final'

	// For identity reveal
	let currentReveal = null; // player whose card is on‐screen
	let showBack = false; // toggle front/back flip

	const podiumDelay = 3000;
	const podiumItemDelay = 3000;
	let podiumPlayers = [];

	async function revealIdentities() {
		for (let idx = 0; idx < players.length; idx++) {
			// show front
			showBack = false;
			currentReveal = players[idx];
			await tick();

			// pause on front
			await new Promise((r) => setTimeout(r, 2000));

			// flip to back
			showBack = true;

			// pause on back + stats
			await new Promise((r) => setTimeout(r, 3000));
		}
		currentReveal = null;
		await tick();
		await new Promise((r) => setTimeout(r, 500));

		startPodiumReveal();
	}

	// Start the podium reveal (up to top 3 human players), always revealing lowest rank first
	function startPodiumReveal() {
		// sort descending and take top 3
		podiumPlayers = [...humanPlayers].sort((a, b) => b.points - a.points).slice(0, 3);

		// reverse so we reveal 3rd→1st (or 2nd→1st if only 2 players, or just 1st)
		const order = [...podiumPlayers].reverse();

		// switch phase immediately so your {#if phase==='podium'} block shows up
		phase = 'podium';

		order.forEach((player, index) => {
			setTimeout(
				() => {
					revealedPodium = [...revealedPodium, player];

					// once the last one is in, wait podiumItemDelay then go to final
					if (index === order.length - 1) {
						setTimeout(() => {
							phase = 'final';
						}, podiumItemDelay);
					}
				},
				podiumItemDelay * (index + 1)
			);
		});
	}

	// return the current users guess from a list of guesses
	function getMyGuess(guesses) {
		return guesses?.find((g) => g.guesser_id === currentUserId) ?? null;
	}

	onMount(() => {
		revealIdentities();
	});

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}
</script>

<Banner>
	{#if phase === 'identity'}
		<h1 class="h3">Tapatybių atskleidimas</h1>
	{:else if phase === 'podium'}
		<h1 class="h3">Podiumas</h1>
	{:else}
		<h1 class="h3">Rezultatai</h1>
	{/if}
</Banner>

<main class="flex h-full w-full flex-col items-center justify-center gap-4 overflow-y-auto p-4">
	{#if phase === 'identity'}
		<div class="relative flex h-80 w-full max-w-md items-center justify-center overflow-hidden">
			{#if currentReveal}
				{#key currentReveal.id}
					<div
						class="absolute flex flex-col gap-3"
						in:fly={{ x: 300, duration: 500 }}
						out:fly={{ x: -300, duration: 500 }}
					>
						<!-- Avatar -->
						{#if currentReveal.assigned_character?.image}
							<img
								src={currentReveal.assigned_character.image}
								alt={currentReveal.assigned_character.name}
								class="mx-auto h-24 w-24 rounded-full object-cover"
							/>
						{/if}

						<!-- Name flip card -->
						<div class="flip-card">
							<div class="flip-card-inner" class:flipped={showBack}>
								<div class="flip-card-front text-center text-xl font-bold">
									{currentReveal.assigned_character?.name}
								</div>
								<div class="flip-card-back text-center text-xl font-bold">
									{currentReveal.username}
								</div>
							</div>
						</div>

						<!-- Stats -->
						<div class="mt-8 text-center text-sm">
							<p class="text-xl">
								Atpažino
								<strong>
									{currentReveal.correctGuesses}
								</strong>
								iš
								<strong>{humanPlayers.length - 1}</strong>
								žaidėjų
							</p>

							{#if currentReveal.id !== currentUserId && currentReveal.guesses}
								{#if getMyGuess(currentReveal.guesses)}
									<p>
										Tu spėjai:
										<span
											class="{getMyGuess(currentReveal.guesses).is_correct
												? 'text-success-500'
												: 'text-error-500'} font-semibold"
										>
											{getMyGuess(currentReveal.guesses).guessed_character_name}
										</span>
									</p>
								{:else}
									<p>Tu spėjai: <span class="text-error-500">–</span></p>
								{/if}
							{:else}
								<p>Tai tu!</p>
							{/if}
						</div>
					</div>
				{/key}
			{/if}
		</div>
	{:else if phase === 'podium'}
		<div class="flex flex-col items-center gap-4">
			{#each revealedPodium as player, i (player.id)}
				<div class="flex w-full max-w-md items-center gap-4 rounded-lg border p-4 shadow">
					<div class="text-2xl font-bold">
						{podiumPlayers.length === 3
							? i === 0
								? '3. vieta'
								: i === 1
									? '2. vieta'
									: '1. vieta'
							: `${i + 1}. vieta`}
					</div>
					<div class="flex flex-col">
						<h4 class="text-xl font-bold">{player.username}</h4>
						<p class="text-md">Taškai: {player.points}</p>
					</div>
				</div>
			{/each}
		</div>
	{:else if phase === 'final'}
		<div class="bg-surface-100-900 grid w-full max-w-xl gap-2 rounded-2xl p-4">
			{#each sortedHumanPlayers as player, i (player.id)}
				<div class="bg-surface-200-800 flex gap-2 rounded-2xl p-4 shadow">
					<header class="flex w-14 flex-col justify-center gap-2 text-center">
						<p title="Vieta" class="text-5xl font-bold">{i + 1}</p>
						{#if player.score_breakdown?.length}
							<Tooltip
								positioning={{
									placement: 'top',
									offset: { mainAxis: 8 },
									flip: true,
									shift: true
								}}
								triggerBase="chip preset-filled-surface-300-700"
								contentBase="card preset-filled-surface-200-800 border border-surface-400-600 shadow-lg p-4 text-start"
								openDelay={100}
							>
								{#snippet trigger()}
									<p>{player.points}</p>
								{/snippet}
								{#snippet content()}
									<h2 class="font-bold">Taškų suvestinė žaidėjui {player.username}</h2>
									<ul class="text-sm">
										{#each player.score_breakdown as line}
											<li><span class="font-semibold">+{line.points}</span> {line.description}</li>
										{/each}
									</ul>
								{/snippet}
							</Tooltip>
						{/if}
					</header>
					<span class="vr border-surface-300-700 border-l-2"></span>
					<div class="flex flex-1 flex-col justify-between">
						<div class="flex flex-col">
							<h4 class="text-xl font-bold">
								{player.username}
							</h4>
							{#if player.assigned_character}
								<p class="text-surface-700-300 italic">
									{player.assigned_character.name}
								</p>
							{:else}
								<p class="text-md italic">Nėra pasirinkto personažo</p>
							{/if}
						</div>
						<div class="flex flex-1 flex-col justify-end">
							<p class="text-sm">
								Buvo atspėtas: <span class="font-semibold"
									>{player.correctGuesses ?? 0}/{humanPlayers.length - 1}</span
								>
							</p>

							{#if player.id !== currentUserId && player.guesses}
								{#if getMyGuess(player.guesses)}
									<p class="text-sm">
										Tu spėjai:
										<span
											class="{getMyGuess(player.guesses).is_correct
												? 'text-success-500'
												: 'text-error-500'} font-semibold"
										>
											{getMyGuess(player.guesses).guessed_character_name}
										</span>
									</p>
								{:else}
									<p class="text-sm">
										Tu spėjai:
										<span class="text-error-500 font-semibold"> - </span>
									</p>
								{/if}
							{/if}
						</div>
					</div>
					<footer class="flex flex-col justify-center">
						{#if player.assigned_character?.image}
							<img
								src={player.assigned_character.image}
								alt={player.assigned_character.name}
								class="h-16 w-16 rounded-full object-cover shadow"
							/>
						{/if}
					</footer>
				</div>
			{/each}
		</div>
		<button class="btn preset-filled-primary-500" on:click={handleLeaveLobby}>
			Noriu žaisti vėl!
		</button>
	{/if}
</main>

<style>
	.flip-card {
		/* give .flip-card a 3D perspective so children rotate correctly */
		perspective: 1000px;
		/* take full width of parent (you already had this) */
		display: block;
		width: 100%;
	}

	.flip-card-inner {
		position: relative; /* establish containing block for abs. children */
		width: 100%; /* fill the parent’s width */
		transform-style: preserve-3d; /* keep children in 3D space */
		transition: transform 0.6s; /* smooth flip */
		/* vendor prefix if you need to support older WebKits */
		-webkit-transform-style: preserve-3d;
	}

	/* when you add the “flipped” class, rotate 180° around the Y axis */
	.flip-card-inner.flipped {
		transform: rotateY(180deg);
		-webkit-transform: rotateY(180deg);
	}

	.flip-card-front,
	.flip-card-back {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		/* hide the “back” of each face when it’s turned away */
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* make it explicit (optional, but can help) */
	.flip-card-front {
		transform: rotateY(0deg);
		z-index: 2; /* keep front on top until flipped */
	}

	.flip-card-back {
		transform: rotateY(180deg);
		z-index: 1;
	}
</style>
