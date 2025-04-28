<script>
	import { Tabs, Slider } from '@skeletonlabs/skeleton-svelte';
	import CollectionsManager from './CollectionsManager.svelte';
	import { createEventDispatcher } from 'svelte';
	import { X, Settings, CircleHelp } from '@lucide/svelte';

	// Props
	let {
		roundLength: initialRoundLength,
		roundCount: initialRoundCount,
		guessTimer: initialGuessTimer,
		selectedCollections
	} = $props();

	const dispatch = createEventDispatcher();

	// Slider state as signals
	let sliderRoundLength = $state([initialRoundLength]);
	let sliderRoundCount = $state([initialRoundCount]);
	let sliderGuessTimer = $state([initialGuessTimer]);

	// Derived values instead of reactive statements
	let roundLength = $derived(sliderRoundLength[0]);
	let roundCount = $derived(sliderRoundCount[0]);
	let guessTimer = $derived(sliderGuessTimer[0]);

	// Tabs state
	let activeTab = $state('gamesettings');

	function handleSave() {
		dispatch('updateSettings', { roundLength, roundCount, guessTimer, selectedCollections });
		dispatch('close');
	}

	function closeModal() {
		dispatch('close');
	}
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
	<div class="bg-surface-100-900 max-w-[80vw] rounded-lg p-6 shadow">
		<Tabs value={activeTab} onValueChange={(e) => (activeTab = e.value)} fluid>
			{#snippet list()}
				<Tabs.Control value="gamesettings"
					>{#snippet lead()}<Settings size={20} />{/snippet}Nustatymai</Tabs.Control
				>
				<Tabs.Control value="questions"
					>{#snippet lead()}<CircleHelp size={20} />{/snippet}Klausimai</Tabs.Control
				>
			{/snippet}

			{#snippet content()}
				<Tabs.Panel value="gamesettings">
					<!-- Raundo ilgis -->
					<div class="mb-10 flex flex-col gap-2">
						<span class="flex items-start gap-2">
							<label class="mb-1 block">Raundo ilgis:</label>
							<span class="chip preset-filled-surface-400-600 -translate-y-0.5">{roundLength}s</span
							>
						</span>
						<Slider
							value={sliderRoundLength}
							min={10}
							max={300}
							step={5}
							markers={[10, 60, 120, 180, 240, 300]}
							onValueChange={(e) => (sliderRoundLength = e.value)}
							meterBg="bg-primary-400"
							thumbRingColor="ring-primary-400"
							trackBg="bg-surface-300-700"
						/>
					</div>

					<!-- Raundų skaičius -->
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
							onValueChange={(e) => (sliderRoundCount = e.value)}
							meterBg="bg-primary-400"
							thumbRingColor="ring-primary-400"
							trackBg="bg-surface-300-700"
						/>
					</div>

					<!-- Laikas spėjimams -->
					<div class="mb-10 flex flex-col gap-2">
						<span class="flex items-start gap-2">
							<label class="mb-1 block">Laikas spėjimams:</label>
							<span class="chip preset-filled-surface-400-600 -translate-y-0.5">{guessTimer}s</span>
						</span>
						<Slider
							value={sliderGuessTimer}
							min={10}
							max={300}
							step={5}
							markers={[10, 60, 120, 180, 240, 300]}
							onValueChange={(e) => (sliderGuessTimer = e.value)}
							meterBg="bg-primary-400"
							thumbRingColor="ring-primary-400"
							trackBg="bg-surface-300-700"
						/>
					</div>

					<!-- Buttons -->
					<div class="flex justify-end space-x-2">
						<button on:click={closeModal} class="btn preset-filled-error-400-600">Atšaukti</button>
						<button on:click={handleSave} class="btn preset-filled-success-400-600"
							>Išsaugoti</button
						>
					</div>
				</Tabs.Panel>

				<Tabs.Panel value="questions">
					<!-- <div class="mb-4 flex items-center justify-between">
						<h2 class="h5">Klausimai</h2>
						<button on:click={closeModal} class="btn hover:preset-filled-surface-300-700 p-2">
							<X size="24" />
						</button>
					</div> -->

					<div class="mb-4 overflow-y-auto">
						<CollectionsManager bind:selectedCollections />
					</div>

					<div class="flex justify-end space-x-2">
						<button on:click={closeModal} class="btn preset-filled-error-400-600">Atšaukti</button>
						<button on:click={handleSave} class="btn preset-filled-success-400-600"
							>Išsaugoti</button
						>
					</div>
				</Tabs.Panel>
			{/snippet}
		</Tabs>
	</div>
</div>
