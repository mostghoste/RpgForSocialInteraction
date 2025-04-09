<script>
	import { createEventDispatcher } from 'svelte';
	import HostSettingsModal from '$lib/HostSettingsModal.svelte';
	import Banner from '$lib/Banner.svelte';
	import { Avatar } from '@skeletonlabs/skeleton-svelte';

	// Props and local state
	export let code;
	export let lobbyState;
	export let players;
	export let isHost;
	export let roundLength;
	export let roundCount;
	export let guessTimer;
	export let availableCollections;
	export let selectedCollections;
	export let availableCharacters;
	export let newCharacterName;
	export let newCharacterDescription;
	export let newCharacterImage;

	const dispatch = createEventDispatcher();
	let showSettingsModal = false;

	function handleModalUpdateSettings(detail) {
		// Relay the updated settings event to the parent
		dispatch('updateSettings', detail);
	}

	function handleStartGame() {
		dispatch('startGame');
	}

	function handleSelectCharacter(charId) {
		dispatch('selectCharacter', { characterId: charId });
	}

	function handleCreateCharacter() {
		dispatch('createCharacter', {
			name: newCharacterName,
			description: newCharacterDescription,
			image: newCharacterImage?.files?.[0] ?? null
		});
	}

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}

	import { Settings } from '@lucide/svelte';
</script>

<Banner>
	<h2 class="h3">Kambario kodas: {code}</h2>
</Banner>

<main class="flex h-full w-full flex-col items-center justify-center gap-4 overflow-scroll pt-16">
	<div class="bg-surface-100-900 flex flex-col rounded-2xl p-4">
		<h2 class="h6">Žaidėjai kambaryje:</h2>
		<ul>
			{#each players as player}
				<li>
					{#if String(player.id) === String(lobbyState.participant_id)}
						<strong>{player.username}</strong>
					{:else}
						{player.username}
					{/if}
					<span>{player.is_host ? ' 👑' : ''}</span>
					<span>{player.characterSelected ? ' ✅' : ''}</span>
				</li>
			{/each}
		</ul>
	</div>

	<div class="bg-surface-100-900 relative flex flex-col rounded-2xl p-4">
		{#if isHost}
			<button class="btn absolute right-2" on:click={() => (showSettingsModal = true)}>
				<Settings />
			</button>
		{/if}
		<h3 class="h6 {isHost ? 'pr-12' : ''}">Žaidimo nustatymai</h3>
		<div class="flex justify-between">
			<p>Raundo ilgis:</p>
			<span>{roundLength}s</span>
		</div>
		<div class="flex justify-between">
			<p>Raundų kiekis:</p>
			<span>{roundCount}</span>
		</div>
		<div class="flex justify-between">
			<p>Laikas spėjimams:</p>
			<span>{guessTimer}s</span>
		</div>
	</div>

	{#if showSettingsModal}
		<HostSettingsModal
			{roundLength}
			{roundCount}
			{guessTimer}
			{availableCollections}
			{selectedCollections}
			on:updateSettings={(e) => handleModalUpdateSettings(e.detail)}
			on:close={() => (showSettingsModal = false)}
		/>
	{/if}

	<div>
		<h3 class="h5">Pasirink savo personažą</h3>
		<div class="bg-surface-100-900 flex max-h-96 flex-col gap-2 rounded-2xl p-4">
			<h4 class="h6">Egzistuojantys personažai:</h4>
			<div class="flex h-full w-full flex-col gap-1 overflow-scroll">
				{#each availableCharacters as char}
					<button
						on:click={() => handleSelectCharacter(char.id)}
						class="bg-surface-200-800 flex gap-4 rounded-2xl p-2"
					>
						<Avatar src={char.image ? char.image : '/fallback_character.jpg'} name={char.name}
						></Avatar>
						<div class="flex flex-col justify-start">
							<p class="text-start font-bold">{char.name}</p>
							<p class="">{char.description}</p>
						</div>
					</button>
				{/each}
			</div>
		</div>
		<div>
			<h4>Sukurti naują personažą:</h4>
			<input
				type="text"
				bind:value={newCharacterName}
				placeholder="Personažo vardas"
				class="input mb-2"
			/>
			<textarea bind:value={newCharacterDescription} placeholder="Aprašymas" class="textarea mb-2"
			></textarea>
			<input type="file" bind:this={newCharacterImage} accept="image/*" class="file-input mb-2" />
			<button on:click={handleCreateCharacter} class="btn btn-primary">Sukurti ir pasirinkti</button
			>
		</div>
	</div>

	<button class="btn border" on:click={handleLeaveLobby}>Palikti kambarį</button>
</main>
