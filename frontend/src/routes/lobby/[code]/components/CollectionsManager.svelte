<script>
	import { user } from '$lib/stores/auth';
	import { toast } from '@zerodevx/svelte-toast';
	import { toastOptions } from '$lib/toastConfig';
	import { onMount, createEventDispatcher } from 'svelte';
	import { apiFetch } from '$lib/api';
	import { Accordion, Segment } from '@skeletonlabs/skeleton-svelte';

	// Icons
	import IconAll from '@lucide/svelte/icons/layers';
	import IconStandard from '@lucide/svelte/icons/book-open';
	import IconUser from '@lucide/svelte/icons/user';
	import IconTrash from '@lucide/svelte/icons/trash';
	import IconAdd from '@lucide/svelte/icons/square-pen';

	export let selectedCollections = [];

	let collections = [];
	let newName = '';
	let newDescription = '';
	let value = [];

	const dispatch = createEventDispatcher();

	// Filter state: 'all', 'standard', 'mine'
	let filterType = 'all';

	// Load all collections
	onMount(async () => {
		const res = await apiFetch('/api/question_collections/');
		if (res.ok) {
			collections = await res.json();
		}
	});

	// Create a new collection
	async function createCollection() {
		if (!newName.trim()) return;
		try {
			const res = await apiFetch('/api/question_collections/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ name: newName, description: newDescription })
			});
			if (!res.ok) throw new Error();
			const created = await res.json();
			collections = [created, ...collections];
			newName = '';
			newDescription = '';
			toast.push('Kolekcija sukurta sėkmingai!', toastOptions.success);
		} catch {
			toast.push('Nepavyko sukurti kolekcijos.', toastOptions.error);
		}
	}

	// Delete a collection
	async function deleteCollection(id) {
		if (!confirm('Ar tikrai nori ištrinti šią klausimų kolekciją?')) return;

		try {
			const res = await apiFetch(`/api/question_collections/${id}/`, { method: 'DELETE' });
			// attempt to parse error body (if any)
			const errData = await res.json().catch(() => ({}));

			if (!res.ok) {
				const msg = errData.error || errData.detail || 'Nepavyko ištrinti kolekcijos.';
				toast.push(msg, toastOptions.error);
				return;
			}

			// on success, remove locally
			collections = collections.filter((c) => c.id !== id);
			value = value.filter((v) => v !== id.toString());
			selectedCollections = selectedCollections.filter((c) => c !== id);
			toast.push('Kolekcija ištrinta.', toastOptions.success);
		} catch (err) {
			toast.push(err.message || 'Nepavyko ištrinti kolekcijos.', toastOptions.error);
		}
	}

	// Add a new question to a collection
	async function addQuestion(collectionId, text) {
		if (!text.trim()) return;
		try {
			const res = await apiFetch(`/api/question_collections/${collectionId}/add_question/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ text })
			});
			if (!res.ok) throw new Error();
			const newQ = await res.json();

			collections = collections.map((c) =>
				c.id === collectionId ? { ...c, questions: [...c.questions, newQ], newQText: '' } : c
			);

			toast.push('Klausimas pridėtas.', toastOptions.success);
		} catch {
			toast.push('Nepavyko pridėti klausimo.', toastOptions.error);
		}
	}

	// Delete a question
	async function deleteQuestion(questionId) {
		try {
			const res = await apiFetch(`/api/questions/${questionId}/`, {
				method: 'DELETE'
			});
			const errData = await res.json().catch(() => ({}));
			if (!res.ok) {
				const msg = errData.error || errData.detail || 'Nepavyko ištrinti klausimo.';
				toast.push(msg, toastOptions.error);
				return;
			}

			// rebuild the entire collections array so Svelte re-renders
			collections = collections.map((c) => ({
				...c,
				questions: c.questions.filter((q) => q.id !== questionId)
			}));

			toast.push('Klausimas ištrintas.', toastOptions.success);
		} catch (err) {
			toast.push(err.message || 'Nepavyko ištrinti klausimo.', toastOptions.error);
		}
	}

	// Derive collections based on filterType
	$: filteredCollections = collections.filter((col) => {
		if (filterType === 'all') return true;
		if (filterType === 'standard') return col.is_standard;
		if (filterType === 'mine') return col.is_mine;
		return true;
	});
</script>

<div>
	<p class="h5 mb-2 ml-2">Klausimų kolekcijos</p>
	<div class="flex flex-col">
		<Segment
			name="collection-filter"
			value={filterType}
			onValueChange={(e) => (filterType = e.value)}
			class="mb-4"
		>
			<Segment.Item value="all">
				<IconAll class="mr-1 inline-block" size={20} /> Visos
			</Segment.Item>
			<Segment.Item value="standard">
				<IconStandard class="mr-1 inline-block" size={20} /> Standartinės
			</Segment.Item>
			<Segment.Item value="mine" disabled={!$user}>
				<IconUser class="mr-1 inline-block" size={20} /> Mano
			</Segment.Item>
		</Segment>
	</div>
</div>

<div class="flex max-h-[60vh] min-h-[60vh] flex-col justify-between gap-4 overflow-y-auto p-4">
	{#if filteredCollections.length === 0}
		<p class="text-surface-500 text-center italic">
			Pagal pasirinktus kriterijus klausimų kolekcijų nerasta
		</p>
	{:else}
		<Accordion collapsible {value} onValueChange={(e) => (value = e.value)}>
			{#each filteredCollections as col (col.id)}
				<Accordion.Item
					value={col.id.toString()}
					controlClasses="hover:bg-surface-950 hover:text-surface-contrast-50-950"
				>
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
								<p class="text-surface-600-400 text-sm">{col.description}</p>
							</div>
						</div>
					{/snippet}

					{#snippet panel()}
						{#if col.questions.length > 0}
							<div class="table-wrap mb-2">
								<table class="table w-full caption-bottom">
									<thead>
										<tr>
											<th class="w-8">Id</th>
											<th>Klausimas</th>
											<th></th>
										</tr>
									</thead>
									<tbody class="[&>tr]:hover:preset-tonal-surface">
										{#each col.questions as q, i (q.id)}
											<tr>
												<td>{i + 1}</td>
												<td>{q.text}</td>
												<td class="text-right">
													{#if $user && !col.is_standard}
														<button
															on:click={() => deleteQuestion(q.id)}
															class="btn btn-sm"
															title="Ištrinti klausimą"
														>
															<IconTrash size={16} />
														</button>
													{/if}
												</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						{:else}
							<p class="mb-4 text-center text-sm">
								Ši klausimų kolekcija dar tuščia. Metas sukurti klausimą!
							</p>
						{/if}

						{#if $user && !col.is_standard}
							<div class="mb-4 flex gap-2">
								<input
									type="text"
									placeholder="Naujas klausimas"
									bind:value={col.newQText}
									class="input flex-1"
								/>
								<button
									class="btn preset-filled-primary-500"
									disabled={!col.newQText?.trim()}
									on:click={() => addQuestion(col.id, col.newQText)}
								>
									<IconAdd size={16} /> Pridėti
								</button>
							</div>
						{/if}

						<div class="mb-2 flex">
							{#if $user && !col.is_standard}
								<button
									on:click={() => deleteCollection(col.id)}
									class="btn btn-sm preset-filled-error-500"
								>
									<IconTrash size={16} /> Ištrinti kolekciją
								</button>
							{/if}
						</div>
					{/snippet}
				</Accordion.Item>
				<hr class="hr" />
			{/each}
		</Accordion>
	{/if}

	{#if $user}
		<div class="flex flex-col gap-2">
			<h4 class="h5">Nauja klausimų kolekcija</h4>
			<div class="flex flex-col gap-2 sm:flex-row">
				<input class="input" placeholder="Pavadinimas" bind:value={newName} />
				<input class="input" placeholder="Aprašymas" bind:value={newDescription} />
				<button
					class="btn preset-filled-primary-500"
					disabled={!newName.trim()}
					on:click={createCollection}
				>
					<IconAdd size={16} /> Sukurti
				</button>
			</div>
		</div>
	{/if}
</div>
