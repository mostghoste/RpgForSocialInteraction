<!-- frontend/src/lib/CharacterUploadModal.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import { FileUpload, Avatar } from '@skeletonlabs/skeleton-svelte';
	import { X } from '@lucide/svelte';

	export let newCharacterName = '';
	export let newCharacterDescription = '';
	export let newCharacterImage = null;

	const dispatch = createEventDispatcher();

	function handleFileUpload(event) {
		console.log(event);
		const file = event.acceptedFiles[0];
		newCharacterImage = file;
		dispatch('filechange', { file });
	}

	function handleFileReject(event) {
		dispatch('filereject', event.detail);
	}

	function createCharacter() {
		dispatch('createCharacter', {
			name: newCharacterName,
			description: newCharacterDescription,
			image: newCharacterImage
		});
		newCharacterName = '';
		newCharacterDescription = '';
		newCharacterImage = null;
	}

	function closeModal() {
		dispatch('close');
	}

	$: isCreateCharacterEnabled =
		newCharacterName &&
		newCharacterName.length >= 3 &&
		newCharacterName.length <= 25 &&
		newCharacterImage;
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
	<div class="bg-surface-100-900 max-w-96 rounded-lg p-6 shadow">
		<div class="mb-4 flex items-center justify-between">
			<h2 class="h5">Naujas personažas</h2>
			<button on:click={closeModal} class="btn hover:preset-filled-surface-300-700 p-2">
				<X size="24" />
			</button>
		</div>

		<div class="mb-4 flex flex-col gap-4">
			<FileUpload
				accept={{ 'image/jpeg': ['.jpeg', '.jpg'], 'image/png': ['.png'] }}
				maxFileSize={1024 * 1024 * 5}
				onFileChange={handleFileUpload}
				onFileReject={handleFileReject}
				class="mb-2"
				label="Įkelk personažo nuotrauką"
				interfaceBg="bg-surface-200-800 hover:bg-surface-300-700"
			/>

			<input
				type="text"
				bind:value={newCharacterName}
				placeholder="Personažo vardas"
				class="input mb-2 w-full text-center"
			/>
		</div>

		<div class="flex justify-end gap-1">
			<button class="btn preset-filled-error-400-600">Atšaukti</button>
			<button
				on:click={createCharacter}
				class="btn preset-filled-success-400-600"
				disabled={!isCreateCharacterEnabled}
			>
				Sukurti ir pasirinkti
			</button>
		</div>
	</div>
</div>
