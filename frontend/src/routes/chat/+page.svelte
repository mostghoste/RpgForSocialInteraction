<script>
	import { onMount } from 'svelte';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	let socket;
	let messages = $state([]);
	let message = $state('');

	onMount(() => {
		console.log('onMount: Creating WebSocket connection to ws://localhost:8000/ws/chat/');
		socket = new WebSocket('ws://localhost:8000/ws/chat/');
		console.log('WebSocket URL:', socket.url);

		socket.onopen = () => {
			console.log('WebSocket connected; readyState:', socket.readyState);
		};

		socket.onmessage = (event) => {
			console.log('WebSocket received event; raw data:', event.data);
			try {
				const parsedData = JSON.parse(event.data);
				console.log('Parsed data:', parsedData);
				if (parsedData.message) {
					messages = [...messages, parsedData.message];
					console.log('Updated messages:', messages);
				} else {
					console.log("Received data does not contain a 'message' property.");
				}
			} catch (err) {
				console.error('Error parsing WebSocket message:', err);
			}
		};

		socket.onerror = (error) => {
			console.error('WebSocket error occurred:', error);
		};

		socket.onclose = (event) => {
			console.log('WebSocket disconnected; code:', event.code, 'reason:', event.reason);
		};
	});

	function sendMessage() {
		console.log('sendMessage called with message:', message);
		if (message.trim().length > 0) {
			if (socket && socket.readyState === WebSocket.OPEN) {
				console.log('Sending message over WebSocket...');
				socket.send(JSON.stringify({ message }));
				console.log('Message sent.');
				message = '';
				console.log('Input cleared.');
			} else {
				console.warn(
					'WebSocket is not open. Current readyState:',
					socket ? socket.readyState : 'undefined'
				);
			}
		} else {
			console.log('sendMessage: Message is empty; nothing to send.');
		}
	}
</script>

<main class="flex h-full flex-col-reverse">
	<input
		class="w-full rounded-3xl bg-[#E7E7E7] px-4 py-2 text-xl placeholder-[#808080]"
		bind:value={message}
		type="text"
		placeholder="Rašyk žinutę"
		onkeydown={(evt) => evt.key === 'Enter' && sendMessage()}
	/>
	<button class="bg-amber-300" onclick={sendMessage}>Send</button>
	<div class="flex flex-col gap-2 pb-4">
		{#each messages as msg}
			<div class="rounded-md bg-white p-2">
				{msg}
			</div>
		{/each}
	</div>
</main>
