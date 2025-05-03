<script>
	import { createEventDispatcher } from 'svelte';
	import HostSettingsModal from './HostSettingsModal.svelte';
	import CharacterUploadModal from './CharacterUploadModal.svelte';
	import Banner from '$lib/Banner.svelte';
	import { Avatar, FileUpload } from '@skeletonlabs/skeleton-svelte';
	import {
		Settings,
		UserRoundPlus,
		LogOut,
		Bot,
		Check,
		Crown,
		VenetianMask,
		User,
		UserX
	} from '@lucide/svelte';
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

	function handleAddNpc() {
		dispatch('addNpc');
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
			<LogOut size={18}></LogOut>
			<span class="hidden sm:hidden md:block">Išeiti</span>
		</button>
		<h2 class="h3 w-full text-center">Kambario kodas: {code}</h2>
		<span class="md:w-30 w-4"></span>
	</div>
</Banner>

<main
	class="flex h-full w-full max-w-3xl flex-col items-center justify-center gap-4 overflow-y-scroll p-2"
>
	<section class="flex w-full flex-col gap-4 md:flex-row">
		<div class="bg-surface-100-900 relative flex w-full flex-1 flex-col rounded-2xl p-4">
			{#if isHost}
				<button
					title="Pridėti AI žaidėją"
					class="btn hover:preset-filled-surface-300-700 absolute right-2 top-2 p-2 hover:scale-105 active:scale-95"
					on:click={handleAddNpc}
				>
					<Bot />
				</button>
			{/if}
			<h2 class="h6">Žaidėjai kambaryje:</h2>
			<ul class="flex flex-col gap-1">
				{#each players as player}
					<li class="flex items-center gap-2">
						{#if player.is_host}
							<span
								class="{player.characterSelected
									? 'bg-success-500 text-success-contrast-500'
									: 'bg-surface-200-800 text-amber-500'} rounded-base p-1 shadow"
								title={'Kambario vadas' +
									(player.characterSelected ? ' | Išsirinko personažą' : '')}
								><Crown size={18} /></span
							>
						{:else if player.is_npc}
							<span
								class="{player.characterSelected
									? 'bg-success-500 text-success-contrast-500'
									: 'bg-surface-200-800 text-tertiary-500'} rounded-base p-1 shadow"
								title="NPC"><Bot size={18} /></span
							>
						{:else}
							<span
								class="{player.characterSelected
									? 'bg-success-500 text-success-contrast-500'
									: 'bg-surface-200-800 text-surface-300'} rounded-base p-1 shadow"
								title={player.characterSelected
									? 'Išsirinko personažą'
									: 'Dar neišsirinko personažo'}><User size={18} /></span
							>
						{/if}
						{#if String(player.id) === String(lobbyState.participant_id)}
							<strong>{player.username}</strong>
						{:else}
							{player.username}
						{/if}
						{#if isHost && String(player.id) !== String(lobbyState.participant_id)}
							<button
								title="Išmesti žaidėją iš kambario"
								class="text-error-500 bg-surface-200-800 rounded-base ml-1 p-1 shadow hover:scale-105 active:scale-95"
								on:click={() =>
									dispatch('kickPlayer', { id: player.id, username: player.username })}
							>
								<UserX size={18} />
							</button>
						{/if}
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
					class="bg-surface-200-800 flex gap-4 rounded-2xl p-2 shadow"
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
