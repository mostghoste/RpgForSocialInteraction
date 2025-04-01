<!-- src/routes/lobby/[code]/components/LobbyInProgress.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';

	export let API_URL;
	export let currentRound;
	export let timeLeft;
	export let chatMessages;
	export let chatInput;

	const dispatch = createEventDispatcher();

	function handleSendMessage() {
		dispatch('sendChatMessage', { text: chatInput });
		chatInput = '';
	}

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}
</script>

{#if currentRound.round_number}
	<div class="round-info" style="margin-bottom: 1rem;">
		<h3>Raundas {currentRound.round_number}</h3>
		<p>Klausimas: {currentRound.question}</p>
		<p>Liko laiko: {timeLeft}s</p>
	</div>
{:else}
	<p>Šiuo metu nėra aktyvaus raundo.</p>
{/if}

<div class="chat-container" style="border: 1px solid #ccc; padding: 1rem;">
	<h3>Game Chat</h3>
	<div class="messages-list" style="max-height: 300px; overflow-y: auto;">
		{#each chatMessages as msg}
			<div
				class="message-item"
				style="margin-bottom: 0.5rem; padding: 0.5rem; border-bottom: 1px solid #eee;"
			>
				<div class="message-sender" style="display: flex; align-items: center;">
					{#if msg.characterImage}
						<img
							src="{API_URL}{msg.characterImage}"
							alt="Char"
							width="40"
							style="margin-right: 0.5rem;"
						/>
					{:else}
						<img
							src="/fallback_character.jpg"
							alt="Fallback"
							width="40"
							style="margin-right: 0.5rem;"
						/>
					{/if}
					<strong>{msg.characterName}:</strong>
				</div>
				<div class="message-text">{msg.text}</div>
				<div class="message-time" style="font-size: 0.8rem; color: #888;">
					{new Date(msg.sentAt).toLocaleTimeString()}
				</div>
			</div>
		{/each}
	</div>
	<div class="message-input" style="margin-top: 0.5rem;">
		<input
			type="text"
			bind:value={chatInput}
			placeholder="Rašyk žinutę..."
			on:keydown={(evt) => evt.key === 'Enter' && handleSendMessage()}
			style="width: 80%; padding: 0.5rem;"
		/>
		<button on:click={handleSendMessage} style="padding: 0.5rem;">Siųsti</button>
	</div>
</div>

<button class="border" on:click={handleLeaveLobby}>Palikti kambarį</button>
