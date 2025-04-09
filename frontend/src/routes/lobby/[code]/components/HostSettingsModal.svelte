<script>
	import { createEventDispatcher } from 'svelte';
	import { Slider } from '@skeletonlabs/skeleton-svelte';
	import { X } from '@lucide/svelte';

	export let roundLength;
	export let roundCount;
	export let guessTimer;
	export let availableCollections = [];
	export let selectedCollections = [];

	const dispatch = createEventDispatcher();

	// Create slider state values from your numeric props.
	let sliderRoundLength = [roundLength];
	let sliderRoundCount = [roundCount];
	let sliderGuessTimer = [guessTimer];

	// Update the exported values when the slider changes.
	$: roundLength = sliderRoundLength[0];
	$: roundCount = sliderRoundCount[0];
	$: guessTimer = sliderGuessTimer[0];

	function handleSave() {
		// Dispatch updated settings along with selected question collections.
		dispatch('updateSettings', { roundLength, roundCount, guessTimer, selectedCollections });
		dispatch('close');
	}

	function closeModal() {
		dispatch('close');
	}
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
	<div class="bg-surface-100-900 max-w-96 rounded-lg p-6 shadow">
		<div class="mb-4 flex items-center justify-between">
			<h2 class="h5">Naujas personažas</h2>
			<button on:click={closeModal} class="btn hover:preset-filled-surface-300-700 p-2">
				<X size="24" />
			</button>
		</div>

		<!-- Slider for Round Length -->
		<div class="mb-10 flex flex-col gap-2">
			<span class="flex items-start gap-2">
				<label class="mb-1 block">Raundo ilgis:</label>
				<span class="chip preset-filled-surface-400-600 -translate-y-0.5">{roundLength}s</span>
			</span>
			<Slider
				value={sliderRoundLength}
				min={10}
				max={300}
				step={5}
				markers={[10, 60, 120, 180, 240, 300]}
				name="roundLength"
				onValueChange={(e) => (sliderRoundLength = e.value)}
				meterBg="bg-primary-400"
				thumbRingColor="ring-primary-400"
				trackBg="bg-surface-300-700"
			/>
		</div>

		<!-- Slider for Round Count -->
		<div class="mb-10 flex flex-col gap-2">
			<span class="flex items-start gap-2">
				<label class="mb-1 block">Raundų skaičius:</label>
				<span class="chip preset-filled-surface-400-600 -translate-y-0.5">{roundCount}</span>
			</span>
			<Slider
				value={sliderRoundCount}
				min={1}
				max={10}
				step={1}
				markers={[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
				name="roundCount"
				onValueChange={(e) => (sliderRoundCount = e.value)}
				meterBg="bg-primary-400"
				thumbRingColor="ring-primary-400"
				trackBg="bg-surface-300-700"
			/>
		</div>

		<!-- Slider for Guess Timer -->
		<div class="mb-10 flex flex-col gap-2">
			<span class="flex items-start gap-2">
				<label class="mb-1 block">Laikas spėjimams:</label>
				<span class="chip preset-filled-surface-400-600 -translate-y-0.5">{guessTimer} s</span>
			</span>
			<Slider
				value={sliderGuessTimer}
				min={10}
				max={300}
				step={5}
				markers={[10, 60, 120, 180, 240, 300]}
				name="guessTimer"
				onValueChange={(e) => (sliderGuessTimer = e.value)}
				meterBg="bg-primary-400"
				thumbRingColor="ring-primary-400"
				trackBg="bg-surface-300-700"
			/>
		</div>

		<!-- Checkbox selection for Question Collections -->
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
				<p class="">Nėra prieinamų klausimų kolekcijų.</p>
			{/if}
		</div>

		<!-- Action Buttons -->
		<div class="flex justify-end space-x-2">
			<button on:click={closeModal} class="btn preset-filled-error-400-600">Atšaukti</button>
			<button on:click={handleSave} class="btn preset-filled-success-400-600">Išsaugoti</button>
		</div>
	</div>
</div>
