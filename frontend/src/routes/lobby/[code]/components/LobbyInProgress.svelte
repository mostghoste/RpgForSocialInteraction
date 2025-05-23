<!-- src/routes/lobby/[code]/components/LobbyInProgress.svelte -->
<script>
	import { createEventDispatcher, afterUpdate } from 'svelte';
	import Banner from '$lib/Banner.svelte';
	import { Send } from '@lucide/svelte';
	import { Avatar } from '@skeletonlabs/skeleton-svelte';

	export let currentRound;
	export let timeLeft;
	export let chatMessages;
	export let chatInput;
	export let myCharacter = null;

	let hasSubmittedMessage = false;
	let prevRoundNumber = null;
	$: if (currentRound && currentRound.round_number !== prevRoundNumber) {
		hasSubmittedMessage = false;
		prevRoundNumber = currentRound.round_number;
	}
	let chatContainer;

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

	// Autoscroll to the bottom of chat when new message is sent
	let previousMessageCount = 0;
	afterUpdate(() => {
		if (chatContainer && chatMessages && chatMessages.length !== previousMessageCount) {
			const distanceFromBottom =
				chatContainer.scrollHeight - (chatContainer.scrollTop + chatContainer.clientHeight);
			if (distanceFromBottom < 4200) {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}
			previousMessageCount = chatMessages.length;
		}
	});
</script>

<Banner variant={hasSubmittedMessage ? 'success' : 'default'}>
	{#if currentRound && timeLeft === 0}
		<h3 class="h3 text-center">Pradedamas sekantis raundas...</h3>
	{:else if hasSubmittedMessage}
		<h3 class="h5">Raundas baigsis už</h3>
		<p class="h3">{timeLeft}s</p>
	{:else if currentRound?.round_number}
		<h3 class="h6">{currentRound.round_number} raundas baigsis už {timeLeft}s</h3>
		<p class="h3 text-center">{currentRound.question}</p>
		{#if myCharacter}
			<p class="mt-1 text-xs">Tu esi:</p>
			<div class="mb-1 flex items-center justify-center gap-2">
				<Avatar
					size="w-6"
					src={myCharacter.image || '/fallback_character.jpg'}
					name={myCharacter.name}
				/>
				<p class="text-sm font-semibold">{myCharacter.name}</p>
			</div>
		{/if}
	{:else}
		<p>Šiuo metu nėra aktyvaus raundo.</p>
	{/if}
</Banner>

<main
	class="flex h-full w-full flex-col items-center justify-center gap-4 overflow-y-scroll md:p-4"
>
	<section
		class="bg-surface-100-900 flex h-full w-full flex-col gap-4 p-2 md:max-w-2xl md:rounded-lg md:p-4"
	>
		<div bind:this={chatContainer} class="flex max-h-full flex-1 flex-col gap-2 overflow-y-auto">
			{#each chatMessages as msg (msg.id)}
				{#if msg.system}
					<!-- System message -->
					<hr class="hr mt-2" />
					<div class="text-center text-sm">
						{@html msg.text}
					</div>
				{:else}
					<!-- Regular chat message -->
					<div class="flex w-full items-end gap-2">
						<Avatar
							src={msg.characterImage ? msg.characterImage : '/fallback_character.jpg'}
							name={msg.characterName}
						></Avatar>
						<div class="flex-1">
							<div
								class="max-w-5/6 bg-surface-900-100 text-surface-contrast-900-100 w-fit whitespace-normal break-words rounded-xl rounded-bl-md px-4 py-2"
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
