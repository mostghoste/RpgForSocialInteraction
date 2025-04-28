<script>
	import { onMount, createEventDispatcher } from 'svelte';
	import { apiFetch } from '$lib/api';
	import { Accordion } from '@skeletonlabs/skeleton-svelte';

	export let selectedCollections = [];

	let collections = [];
	let newName = '';
	let newDescription = '';
	let value = []; // track open panels by their `value`

	const dispatch = createEventDispatcher();

	// Load all of the host’s collections (plus public)
	onMount(async () => {
		const res = await apiFetch('/api/question_collections/');
		if (res.ok) {
			collections = await res.json();
		}
	});

	// Create a new collection
	async function createCollection() {
		if (!newName.trim()) return;
		const res = await apiFetch('/api/question_collections/', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ name: newName, description: newDescription })
		});
		if (res.ok) {
			const created = await res.json();
			collections = [created, ...collections];
			newName = '';
			newDescription = '';
		}
	}

	// Delete a collection
	async function deleteCollection(id) {
		if (!confirm('Really delete this collection?')) return;
		const res = await apiFetch(`/api/question_collections/${id}/`, { method: 'DELETE' });
		if (res.ok) {
			collections = collections.filter((c) => c.id !== id);
			// also remove it from the open panels if it was open
			value = value.filter((v) => v !== id.toString());
		}
	}

	// Add a new question to a collection
	async function addQuestion(collectionId, text) {
		if (!text.trim()) return;
		const res = await apiFetch(`/api/question_collections/${collectionId}/add_question/`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ text })
		});
		if (res.ok) {
			const newQ = await res.json();
			const col = collections.find((c) => c.id === collectionId);
			col.questions = [...col.questions, newQ];
			col.newQText = '';
		}
	}

	// Delete a question
	async function deleteQuestion(questionId) {
		await apiFetch(`/api/questions/${questionId}/`, { method: 'DELETE' });
		collections.forEach((c) => {
			c.questions = c.questions.filter((q) => q.id !== questionId);
		});
	}
</script>

<div class="flex max-h-[60vh] flex-col gap-4 overflow-y-auto p-4">
	<!-- new‐collection form (unchanged) -->
	<div class="flex gap-2">
		<input type="text" placeholder="Pavadinimas" bind:value={newName} class="input flex-1" />
		<input type="text" placeholder="Aprašymas" bind:value={newDescription} class="input flex-2" />
		<button on:click={createCollection} class="btn preset-filled">Sukurti</button>
	</div>

	<Accordion collapsible {value} onValueChange={(e) => (value = e.value)}>
		{#each collections as col (col.id)}
			<Accordion.Item value={col.id.toString()}>
				{#snippet control()}
					<div class="flex items-center">
						<input
							type="checkbox"
							id="qc-{col.id}"
							class="checkbox mr-4"
							bind:group={selectedCollections}
							value={col.id}
							on:click|stopPropagation
						/>
						<div>
							<h3 class="font-bold">{col.name}</h3>
							<p>{col.description}</p>
						</div>
					</div>
				{/snippet}
				{#snippet panel()}
					<!-- delete collection button -->
					<div class="mb-2 flex justify-end">
						<button on:click={() => deleteCollection(col.id)} class="btn-sm error">
							Ištrinti kolekciją
						</button>
					</div>
					<!-- existing questions list and add‐question UI -->
					<ul class="mb-2 list-disc pl-4">
						{#each col.questions as q (q.id)}
							<li class="flex items-center justify-between">
								<span>{q.text}</span>
								<button on:click={() => deleteQuestion(q.id)} class="btn-sm error">×</button>
							</li>
						{/each}
					</ul>
					<div class="flex gap-2">
						<input
							type="text"
							placeholder="Naujas klausimas"
							bind:value={col.newQText}
							class="input flex-1"
						/>
						<button on:click={() => addQuestion(col.id, col.newQText)} class="btn-sm">
							Pridėti
						</button>
					</div>
				{/snippet}
			</Accordion.Item>
			<hr class="hr" />
		{/each}
	</Accordion>
</div>
