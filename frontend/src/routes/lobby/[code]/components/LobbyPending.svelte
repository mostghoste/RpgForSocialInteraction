<script>
	import { createEventDispatcher } from 'svelte';
	import HostSettingsModal from '$lib/HostSettingsModal.svelte';
	import Banner from '$lib/Banner.svelte';
	import { Avatar, FileUpload } from '@skeletonlabs/skeleton-svelte';
	import { Settings } from '@lucide/svelte';

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
			image: newCharacterImage ?? null
		});
	}

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}

	function handleFileUpload(event) {
		let file = event.acceptedFiles[0];
		newCharacterImage = file;
	}

	function handleFileReject(event) {
		console.error('Netinkamas failas:', event.detail);
	}

	$: isCreateCharacterEnabled =
		newCharacterName &&
		newCharacterName.length >= 3 &&
		newCharacterName.length <= 25 &&
		newCharacterImage;
</script>

<Banner>
	<h2 class="h3">Kambario kodas: {code}</h2>
</Banner>

<main class="flex h-full w-full flex-col items-center justify-center gap-4 overflow-y-scroll pt-48">
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
					<span title="Kambario vadas">{player.is_host ? ' 👑' : ''}</span>
					<span title="Išsirinko veikėją">{player.characterSelected ? ' ✅' : ''}</span>
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
	<div class="bg-surface-100-900 flex max-h-96 flex-col gap-2 rounded-2xl p-4">
		<h4 class="h6">Sukurk savo veikėją!</h4>
		<!-- Use the FileUpload component with validation for only jpg/png images up to 5MB -->
		<FileUpload
			accept={{ 'image/jpeg': ['.jpeg', '.jpg'], 'image/png': ['.png'] }}
			maxFileSize={1024 * 1024 * 5}
			onFileChange={handleFileUpload}
			onFileReject={handleFileReject}
			class="mb-2"
		/>
		<input
			type="text"
			bind:value={newCharacterName}
			placeholder="Personažo vardas"
			class="input mb-2"
		/>
		<textarea bind:value={newCharacterDescription} placeholder="Aprašymas" class="textarea mb-2"
		></textarea>

		<button
			on:click={handleCreateCharacter}
			class="btn preset-filled-success-400-600"
			disabled={!isCreateCharacterEnabled}
		>
			Sukurti ir pasirinkti
		</button>
	</div>

	<button class="btn preset-filled-error-400-600" on:click={handleLeaveLobby}
		>Palikti kambarį</button
	>
</main>
