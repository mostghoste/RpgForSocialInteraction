<script>
	import { createEventDispatcher } from 'svelte';
	import HostSettingsModal from './HostSettingsModal.svelte';
	import CharacterUploadModal from './CharacterUploadModal.svelte';
	import Banner from '$lib/Banner.svelte';
	import { Avatar, FileUpload } from '@skeletonlabs/skeleton-svelte';
	import { Settings, UserRoundPlus, LogOut } from '@lucide/svelte';
	import { toast } from '@zerodevx/svelte-toast';
	import { toastOptions } from '$lib/toastConfig';

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
	let showCharacterModal = false;

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
		const { file } = event.detail;
		newCharacterImage = file;
	}

	function handleFileReject() {
		toast.push('Nepavyko įkelti failo.', toastOptions.error);
	}

	$: isCreateCharacterEnabled =
		newCharacterName &&
		newCharacterName.length >= 3 &&
		newCharacterName.length <= 25 &&
		newCharacterImage;
</script>

<Banner>
	<div class="flex w-full">
		<button
			class="btn btn-sm preset-filled-primary-400-600 hover:scale-105 active:scale-95"
			title="Palikti kambarį"
			on:click={handleLeaveLobby}
		>
			<LogOut size={20}></LogOut>
			<span class="hidden sm:hidden md:block"> Palikti kambarį</span>
		</button>
		<h2 class="h3 w-full text-center">Kambario kodas: {code}</h2>
		<span class="sm:w-16 md:w-48"></span>
	</div>
</Banner>

<main
	class="flex h-full w-full max-w-3xl flex-col items-center justify-center gap-4 overflow-y-scroll p-2"
>
	<section class="flex w-full flex-col gap-4 md:flex-row">
		<div class="bg-surface-100-900 flex w-full flex-1 flex-col rounded-2xl p-4">
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

		<div class="bg-surface-100-900 relative flex w-full flex-1 flex-col rounded-2xl p-4">
			{#if isHost}
				<button
					title="Žaidimo nustatymai"
					class="btn hover:preset-filled-surface-300-700 absolute right-2 top-2 p-2 hover:scale-105 active:scale-95"
					on:click={() => (showSettingsModal = true)}
				>
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
			{#if isHost}
				<!-- Start game button added for host -->
				<div class="mt-4 flex justify-center">
					<button
						class="btn preset-filled-success-400-600 hover:scale-105 active:scale-95"
						on:click={handleStartGame}
					>
						Pradėti žaidimą
					</button>
				</div>
			{/if}
		</div>
	</section>

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

	<div class="bg-surface-100-900 relative flex max-h-96 w-full flex-col gap-2 rounded-2xl p-4">
		<h4 class="h6">Išsirink personažą:</h4>
		<button
			title="Sukurti naują veikėją"
			class="btn hover:preset-filled-surface-300-700 absolute right-4 top-3 rounded-sm p-2 hover:scale-105 active:scale-95"
			on:click={() => (showCharacterModal = true)}
		>
			<UserRoundPlus></UserRoundPlus>
		</button>
		<div class="flex h-full w-full flex-col gap-1 overflow-scroll">
			{#each availableCharacters as char}
				<button
					on:click={() => handleSelectCharacter(char.id)}
					class="bg-surface-200-800 flex gap-4 rounded-2xl p-2"
				>
					<Avatar src={char.image ? char.image : '/fallback_character.jpg'} name={char.name}
					></Avatar>
					<div class="flex flex-1 flex-col justify-start">
						<p class="text-start font-bold">{char.name}</p>
						<p class="text-start">{char.description}</p>
					</div>
				</button>
			{/each}
		</div>
	</div>
	{#if showCharacterModal}
		<CharacterUploadModal
			bind:newCharacterName
			bind:newCharacterDescription
			bind:newCharacterImage
			on:createCharacter={(e) => {
				handleCreateCharacter(e.detail);
				showCharacterModal = false;
			}}
			on:close={() => (showCharacterModal = false)}
			on:filechange={handleFileUpload}
			on:filereject={handleFileReject}
		/>
	{/if}
</main>
