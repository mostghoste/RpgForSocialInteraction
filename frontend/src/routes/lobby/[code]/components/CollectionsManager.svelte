<script>
	import { onMount, createEventDispatcher } from 'svelte';
	import { apiFetch } from '$lib/api';
	import { Accordion } from '@skeletonlabs/skeleton-svelte';

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

<div class="flex max-h-[80vh] flex-col gap-4 overflow-y-auto p-4">
	<h2 class="h5">Klausimai</h2>

	<!-- New collection form -->
	<div class="flex gap-2">
		<input type="text" placeholder="Pavadinimas" bind:value={newName} class="input flex-1" />
		<input type="text" placeholder="Aprašymas" bind:value={newDescription} class="input flex-2" />
		<button on:click={createCollection} class="btn preset-filled">Sukurti</button>
	</div>

	<Accordion type="multiple" {value} onValueChange={(e) => (value = e.value)}>
		{#each collections as col (col.id)}
			<Accordion.Item value={col.id.toString()}>
				{#snippet control()}
					<strong>{col.name}</strong> — {col.description}
				{/snippet}
				{#snippet panel()}
					<div class="mb-2 flex justify-end">
						<button on:click={() => deleteCollection(col.id)} class="btn-sm error">
							Ištrinti kolekciją
						</button>
					</div>

					<ul class="mb-2 list-disc pl-4">
						{#each col.questions as q (q.id)}
							<li class="flex items-center justify-between">
								<span>{q.text}</span>
								<button on:click={() => deleteQuestion(q.id)} class="btn-sm error"> × </button>
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

	<button on:click={() => dispatch('close')} class="btn-secondary mt-4"> Uždaryti </button>
</div>
