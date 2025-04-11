<!-- src/routes/lobby/[code]/components/LobbyInProgress.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';

	export let API_URL;
	export let currentRound;
	export let timeLeft;
	export let chatMessages;
	export let chatInput;

	let hasSubmittedMessage = false;

	const dispatch = createEventDispatcher();

	function handleSendMessage() {
		if (!hasSubmittedMessage) {
			hasSubmittedMessage = true;
		}
		dispatch('sendChatMessage', { text: chatInput });
		chatInput = '';
	}

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}

	// Compute a list that interleaves round divider items.
	function computeDisplayedMessages(messages) {
		let result = [];
		if ((!messages || messages.length === 0) && currentRound && currentRound.round_number) {
			// If no messages yet, insert only the start divider for the current round.
			result.push({
				type: 'divider-start',
				roundNumber: currentRound.round_number,
				question: currentRound.question
			});
			return result;
		}
		// Make sure messages are sorted by sentAt (if not already)
		const sorted = [...messages].sort((a, b) => new Date(a.sentAt) - new Date(b.sentAt));
		let currentGroup = null;
		sorted.forEach((msg, i) => {
			// When a new round group starts, insert a divider at the beginning.
			if (!currentGroup || currentGroup.roundNumber !== msg.roundNumber) {
				// if this is not the first group then push an end divider for the previous round
				if (currentGroup) {
					result.push({
						type: 'divider-end',
						roundNumber: currentGroup.roundNumber
					});
				}
				currentGroup = {
					roundNumber: msg.roundNumber,
					question:
						currentRound && parseInt(msg.roundNumber) === currentRound.round_number
							? currentRound.question
							: ''
				};
				result.push({
					type: 'divider-start',
					roundNumber: msg.roundNumber,
					question: currentGroup.question
				});
			}
			result.push({ type: 'message', data: msg });
		});
		// Add an end divider for the last group
		if (currentGroup) {
			result.push({
				type: 'divider-end',
				roundNumber: currentGroup.roundNumber
			});
		}
		return result;
	}

	// Recompute the displayed messages when chatMessages changes.
	$: displayedMessages = computeDisplayedMessages(chatMessages);
</script>

<!-- Use a different Banner variant if the user has already sent a message -->
<Banner variant={hasSubmittedMessage ? 'success' : 'default'}>
	{#if hasSubmittedMessage}
		<h3 class="h3">Liko laiko: {timeLeft}s</h3>
	{:else if currentRound?.round_number}
		<h3 class="h3">{currentRound.round_number} raundas</h3>
		<p>Klausimas: {currentRound.question}</p>
		<p>Liko laiko: {timeLeft}s</p>
	{:else}
		<p>Šiuo metu nėra aktyvaus raundo.</p>
	{/if}
</Banner>
<main class="flex h-full flex-col items-center justify-center gap-4 overflow-y-scroll p-4">
	<section class="bg-surface-100-900 h-full w-full max-w-2xl rounded-lg p-4">
		<h3 class="mb-2 text-xl font-semibold">Pokalbio langas</h3>
		<div class="flex max-h-72 flex-col gap-2 overflow-y-auto">
			{#each displayedMessages as item}
				{#if item.type === 'divider-start'}
					<!-- Round start divider -->
					<div class="my-2 text-center text-sm">
						{item.roundNumber} raundas prasidėjo. {item.question ? item.question : ''}
					</div>
				{:else if item.type === 'divider-end'}
					<!-- Round end divider -->
					<div class="my-2 text-center text-sm">
						{item.roundNumber} raundas pasibaigė
					</div>
				{:else if item.type === 'message'}
					<!-- Regular chat message -->
					<div class="rounded-md p-2">
						<div class="mb-1 flex items-center">
							{#if item.data.characterImage}
								<img src="{API_URL}{item.data.characterImage}" alt="Char" width="40" class="mr-2" />
							{:else}
								<img src="/fallback_character.jpg" alt="Fallback" width="40" class="mr-2" />
							{/if}
							<strong>{item.data.characterName}:</strong>
						</div>
						<div class="">{item.data.text}</div>
						<div class="mt-1 text-xs">
							{new Date(item.data.sentAt).toLocaleTimeString()}
						</div>
					</div>
				{/if}
			{/each}
		</div>
		<footer class="mt-4 flex items-center gap-2">
			<input
				type="text"
				bind:value={chatInput}
				placeholder="Rašyk žinutę..."
				on:keydown={(evt) => evt.key === 'Enter' && handleSendMessage()}
				class="w-full rounded-3xl bg-[#E7E7E7] px-4 py-2 text-xl placeholder-gray-500 focus:outline-none"
			/>
			<button on:click={handleSendMessage} class="rounded-lg bg-amber-300 px-4 py-2 text-lg">
				Siųsti
			</button>
		</footer>
	</section>
</main>
