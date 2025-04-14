<!-- src/routes/lobby/[code]/components/LobbyInProgress.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';
	import { Send } from '@lucide/svelte';
	import { Avatar } from '@skeletonlabs/skeleton-svelte';

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

<Banner variant={hasSubmittedMessage ? 'success' : 'default'}>
	{#if hasSubmittedMessage}
		<h3 class="h3">Liko laiko: {timeLeft}s</h3>
	{:else if currentRound?.round_number}
		<h3 class="h3">{currentRound.round_number} raundas</h3>
		<p class="text-center">{currentRound.question}</p>
		<p class="text-sm">Liko laiko: {timeLeft}s</p>
	{:else}
		<p>Šiuo metu nėra aktyvaus raundo.</p>
	{/if}
</Banner>

<main class="flex h-full flex-col items-center justify-center gap-4 overflow-y-scroll md:p-4">
	<section
		class="bg-surface-100-900 flex h-full w-full flex-col gap-4 p-2 md:max-w-2xl md:rounded-lg md:p-4"
	>
		<h3 class="mb-2 text-xl font-semibold">Pokalbio langas</h3>
		<div class="flex max-h-full flex-1 flex-col gap-2 overflow-y-auto">
			{#each chatMessages as msg (msg.id)}
				{#if msg.system}
					<!-- System message -->
					<hr class="hr mt-2" />
					<div class="text-center text-sm">
						{@html msg.text}
					</div>
				{:else}
					<!-- Regular chat message -->
					<div class="flex w-full gap-2">
						<Avatar
							src={msg.characterImage ? msg.characterImage : '/fallback_character.jpg'}
							name={msg.characterName}
						></Avatar>
						<div class="flex-1">
							<div
								class="max-w-5/6 bg-surface-900-100 text-surface-contrast-900-100 w-fit break-all rounded-xl rounded-bl-md px-4 py-2"
							>
								<p><strong>{msg.characterName}</strong></p>
								<p class="text-wrap" title={new Date(msg.sentAt).toLocaleTimeString()}>
									{msg.text}
								</p>
							</div>
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
