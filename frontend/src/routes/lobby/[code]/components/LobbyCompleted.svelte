<script>
	import { onMount, tick, createEventDispatcher } from 'svelte';
	import { fly } from 'svelte/transition';
	import Banner from '$lib/Banner.svelte';
	import { Tooltip } from '@skeletonlabs/skeleton-svelte';

	export let players = [];
	export let currentUserId;

	const dispatch = createEventDispatcher();

	$: humanPlayers = players.filter((p) => !p.is_npc);
	$: sortedHumanPlayers = [...humanPlayers].sort((a, b) => b.points - a.points);

	let revealedPlayers = [];

	let phase = 'identity'; // phases: 'identity', 'podium', 'final'

	// For identity reveal
	let currentReveal = null; // player whose card is on‐screen
	let showBack = false; // toggle front/back flip
	let currentPlayerGuess = null;
	let guessedPlayer = null;

	$: {
		if (currentReveal && currentReveal.id !== currentUserId && currentReveal.guesses?.length) {
			currentPlayerGuess = getMyGuess(currentReveal.guesses);
			guessedPlayer = players.find(
				(p) => p.assigned_character?.name === currentPlayerGuess.guessed_character_name
			);
		} else {
			currentPlayerGuess = null;
			guessedPlayer = null;
		}
	}

	$: totalGuessers = currentReveal
		? currentReveal.is_npc
			? humanPlayers.length
			: humanPlayers.length - 1
		: 0;

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

			// pause on back
			await new Promise((r) => setTimeout(r, 3000));
		}

		await tick();
		await new Promise((r) => setTimeout(r, 500));
		currentReveal = null;
		startPodiumReveal();
	}

	let rectangleHeights = {};
	let nameRevealed = {};
	const podiumItemDelay = 2000;
	let podiumPlayers = [];
	$: layoutPlayers =
		podiumPlayers.length === 3
			? [podiumPlayers[1], podiumPlayers[0], podiumPlayers[2]]
			: podiumPlayers.length === 2
				? [podiumPlayers[1], podiumPlayers[0]]
				: podiumPlayers;

	// rank to bar colour
	function getPodiumColor(player) {
		const rank = podiumPlayers.indexOf(player);
		return rank === 0 ? 'bg-yellow-400' : rank === 1 ? 'bg-gray-300' : 'bg-amber-700';
	}

	// rank to bar height
	function getPodiumHeight(player) {
		const rank = podiumPlayers.indexOf(player);
		return [230, 130, 100][rank] || 80;
	}

	function startPodiumReveal() {
		// sort descending and take top 3 then reverse
		podiumPlayers = [...humanPlayers].sort((a, b) => b.points - a.points).slice(0, 3);
		const order = [...podiumPlayers].reverse();

		phase = 'podium';

		order.forEach((player, index) => {
			// stagger each reveal by podiumItemDelay
			setTimeout(
				() => {
					// grow the bar after a tiny pause
					setTimeout(() => {
						rectangleHeights[player.id] = getPodiumHeight(player);

						// reveal name after the bar animation
						setTimeout(() => {
							nameRevealed[player.id] = true;

							// once the last name is shown wait then switch phase
							if (index === order.length - 1) {
								setTimeout(() => {
									phase = 'final';
								}, 5000);
							}
						}, 1000);
					}, 200);
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
		// startPodiumReveal();
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
		<div class="h-120 relative flex w-full max-w-md items-center justify-center overflow-hidden">
			{#if currentReveal}
				<div class="absolute inset-0 flex items-center justify-center">
					<div
						class="bg-surface-600 scale-y-20 w-100 h-64 translate-y-5 rounded-full blur-md"
					></div>
				</div>
				<div
					class="pointer-events-none absolute inset-0 flex translate-y-6 rotate-45 items-center justify-center"
				>
					<div
						class="h-80 w-80"
						style="background: linear-gradient(
					to bottom right,
					rgba(245,158,11,0.4) 0%,
					rgba(245,158,11,0)   50%
				  );"
					></div>
				</div>
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
								class="mx-auto h-24 w-24 rounded-full object-cover shadow-lg"
							/>
						{/if}

						<!-- Name flip card -->
						<div class="flip-card">
							<div class="flip-card-inner" class:flipped={showBack}>
								<div class="flip-card-front whitespace-nowrap text-center text-xl font-bold">
									{currentReveal.assigned_character?.name}
								</div>
								<div class="flip-card-back whitespace-nowrap text-center text-xl font-bold">
									{currentReveal.username}
									{#if currentReveal.is_npc}
										🤖{/if}
								</div>
							</div>
						</div>

						<!-- Stats -->
						<div class="mt-10 text-center text-sm">
							<p class="text-xl">
								Atpažino
								<strong>
									{currentReveal.correctGuesses}
								</strong>
								iš
								<strong>{totalGuessers}</strong>
								žaidėjų
							</p>

							{#if currentReveal.id === currentUserId}
								<p class="text-lg font-semibold">Tai tu!</p>
							{:else if currentPlayerGuess}
								<p>
									Tu spėjai:
									<span
										class="{currentPlayerGuess.is_correct
											? 'text-success-500'
											: 'text-error-500'} font-semibold"
									>
										{#if guessedPlayer}
											{guessedPlayer.is_npc ? 'Robotas' : guessedPlayer.username}
										{:else}
											{currentPlayerGuess.guessed_character_name}
										{/if}
									</span>
								</p>
							{/if}
						</div>
					</div>
				{/key}
			{/if}
		</div>
	{:else if phase === 'podium'}
		<div class="relative flex h-[250px] w-full flex-row items-end justify-center gap-8">
			<div class="absolute inset-x-0 bottom-0 flex items-end justify-center">
				<div
					class="bg-surface-600 scale-y-30 translate-y-45 h-100 w-100 z-10 rounded-full blur-sm"
				></div>
			</div>
			{#each layoutPlayers as player, i (player.id)}
				<div class="relative z-20 flex flex-col items-center">
					<!-- name flies in above the bar -->
					{#if nameRevealed[player.id]}
						<p
							class="absolute -top-10 left-1/2 -translate-x-1/2 whitespace-nowrap text-center font-bold {i ===
							1
								? 'animate-bounce-from-bottom'
								: ''}"
							class:text-xl={player.username.length <= 12}
							class:text-lg={player.username.length > 12 && player.username.length <= 16}
							class:text-md={player.username.length > 16}
							in:fly={{ y: -10, duration: 400 }}
						>
							{player.username}
						</p>
					{/if}

					<!-- bar + points at top -->
					<div class="w-24 overflow-hidden rounded-t-xl">
						<div
							class={`flex flex-col items-center justify-start transition-all duration-1000 ease-out ${getPodiumColor(player)}`}
							style="height: {rectangleHeights[player.id] ?? 0}px"
						>
							{#if rectangleHeights[player.id]}
								<span class="mt-1 text-lg font-bold">
									{player.points}
								</span>
							{/if}
						</div>
					</div>

					<!-- place labels -->
					<p class="mt-2 text-center text-sm font-semibold">
						{i === 0 ? '2 vieta' : i === 1 ? '1 vieta' : '3 vieta'}
					</p>
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
		perspective: 1000px;
		display: block;
		width: 100%;
	}

	.flip-card-inner {
		position: relative;
		width: 100%;
		transform-style: preserve-3d;
		transition: transform 0.6s;
		-webkit-transform-style: preserve-3d;
	}

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
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.flip-card-front {
		transform: rotateY(0deg);
		z-index: 2;
	}

	.flip-card-back {
		transform: rotateY(180deg);
		z-index: 1;
	}

	@keyframes bounce-from-bottom {
		0%,
		100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(-25%);
		}
	}

	.animate-bounce-from-bottom {
		animation: bounce-from-bottom 1s ease-in-out infinite;
		animation-delay: 0.4s;
		animation-fill-mode: both;
	}
</style>
