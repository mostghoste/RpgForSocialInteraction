<!-- src/routes/lobby/[code]/components/LobbyInProgress.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';
	import { Send } from '@lucide/svelte';

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
</script>

<!-- Use a different Banner variant if the user has already sent a message -->
<Banner variant={hasSubmittedMessage ? 'success' : 'default'}>
	{#if hasSubmittedMessage}
		<h3 class="h3">Liko laiko: {timeLeft}s</h3>
	{:else if currentRound?.round_number}
		<h3 class="h3">{currentRound.round_number} raundas</h3>
		<p class="">{currentRound.question}</p>
		<p class="text-sm">Liko laiko: {timeLeft}s</p>
	{:else}
		<p>Šiuo metu nėra aktyvaus raundo.</p>
	{/if}
</Banner>
<main class="flex h-full flex-col items-center justify-center gap-4 overflow-y-scroll p-4">
	<section class="bg-surface-100-900 h-full w-full max-w-2xl rounded-lg p-4">
		<h3 class="mb-2 text-xl font-semibold">Pokalbio langas</h3>
		<div class="flex max-h-full flex-col gap-2 overflow-y-auto">
			{#each chatMessages as msg (msg.id)}
				{#if msg.system}
					<!-- System message: Render as a divider or banner -->
					<div class="my-2 text-center text-sm italic text-red-600">
						{msg.text}
					</div>
				{:else}
					<!-- Regular chat message -->
					<div class="rounded-md border p-2">
						<div class="mb-1 flex items-center">
							{#if msg.characterImage}
								<img src="{API_URL}{msg.characterImage}" alt="Char" width="40" class="mr-2" />
							{:else}
								<img src="/fallback_character.jpg" alt="Fallback" width="40" class="mr-2" />
							{/if}
						</div>
						<div>
							<p><strong>{msg.characterName}:</strong></p>
							<p title={new Date(msg.sentAt).toLocaleTimeString()}>{msg.text}</p>
						</div>
					</div>
				{/if}
			{/each}
		</div>
		<footer class="flex">
			<input
				type="text"
				bind:value={chatInput}
				placeholder="Rašyk žinutę..."
				on:keydown={(evt) => evt.key === 'Enter' && handleSendMessage()}
				class="placeholder-surface-500 bg-surface-100 text-surface-contrast-100 w-full rounded-l-3xl px-4 py-2 text-xl focus:outline-none"
			/>
			<button
				on:click={handleSendMessage}
				class="ig-btn bg-surface-100 rounded-r-3xl"
				title="Siųsti žinutę"
			>
				<Send size={24} color="#8B3399" />
			</button>
		</footer>
	</section>
</main>
