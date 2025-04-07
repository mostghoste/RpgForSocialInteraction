<script>
	import { createEventDispatcher } from 'svelte';
	export let roundLength;
	export let roundCount;
	export let guessTimer;
	export let availableCollections = [];
	export let selectedCollections = [];
	const dispatch = createEventDispatcher();

	function handleSave() {
		// Dispatch all updated settings (including selected collections)
		dispatch('updateSettings', { roundLength, roundCount, guessTimer, selectedCollections });
		dispatch('close');
	}

	function handleCancel() {
		dispatch('close');
	}
</script>

<div class="bg-surface-100-900/75 fixed inset-0 z-50 flex items-center justify-center">
	<div class="bg-surface-200-800 max-w-96 rounded-lg p-6 shadow">
		<h2 class="mb-4 text-xl font-bold">Kambario nustatymai</h2>
		<div class="mb-4">
			<label class="mb-1 block">Raundo ilgis (s):</label>
			<input
				type="number"
				bind:value={roundLength}
				min="1"
				class="w-full rounded border border-gray-300 p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
		</div>
		<div class="mb-4">
			<label class="mb-1 block">Raundų skaičius:</label>
			<input
				type="number"
				bind:value={roundCount}
				min="1"
				class="w-full rounded border border-gray-300 p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
		</div>
		<div class="mb-4">
			<label class="mb-1 block">Laikas spėjimams (s):</label>
			<input
				type="number"
				bind:value={guessTimer}
				min="1"
				class="w-full rounded border border-gray-300 p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
		</div>
		<div class="mb-4">
			<h3 class="mb-2 text-lg font-semibold">Naudojami klausimai</h3>
			{#if availableCollections.length > 0}
				{#each availableCollections as collection}
					<div class="mb-1 flex items-center">
						<input
							type="checkbox"
							id="qc-{collection.id}"
							value={collection.id}
							bind:group={selectedCollections}
							class="mr-2"
						/>
						<label for="qc-{collection.id}">{collection.name}</label>
					</div>
				{/each}
			{:else}
				<p class="text-gray-500">Nėra prieinamų klausimų kolekcijų.</p>
			{/if}
		</div>
		<div class="flex justify-end space-x-2">
			<button on:click={handleSave} class="btn preset-filled-success-500"> Išsaugoti </button>
			<button on:click={handleCancel} class="btn preset-filled-error-500"> Atšaukti </button>
		</div>
	</div>
</div>
