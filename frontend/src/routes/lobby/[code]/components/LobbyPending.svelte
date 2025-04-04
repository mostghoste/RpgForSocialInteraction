<!-- src/routes/lobby/[code]/components/LobbyPending.svelte -->
<script>
	import { createEventDispatcher } from 'svelte';
	import Banner from '$lib/Banner.svelte';

	export let code;
	export let lobbyState; // full state if needed
	export let players;
	export let isHost;
	export let roundLength;
	export let roundCount;
	export let guessTimer;
	export let availableCollections;
	export let selectedCollections; // array of collection IDs
	export let availableCharacters;
	export let newCharacterName;
	export let newCharacterDescription;
	export let newCharacterImage;

	const dispatch = createEventDispatcher();

	function handleUpdateSettings() {
		dispatch('updateSettings', { roundLength, roundCount, guessTimer });
	}

	function handleUpdateCollections() {
		dispatch('updateCollections', { collections: selectedCollections });
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
			image: newCharacterImage?.files?.[0] ?? null
		});
	}

	function handleLeaveLobby() {
		dispatch('leaveLobby');
	}
</script>

<Banner>
	<h2>Kambario kodas: {code}</h2>
</Banner>
<main class="flex h-full flex-col items-center justify-center">
	<p>Žaidėjai kambaryje:</p>
	<ul>
		{#each players as player}
			<li>
				{#if String(player.id) === String(lobbyState.participant_id)}
					<strong>{player.username}</strong>
				{:else}
					{player.username}
				{/if}
				{#if player.is_host}
					<span> 👑</span>
				{/if}
				{player.characterSelected ? ' ✅' : ''}
			</li>
		{/each}
	</ul>

	<p>Spėjimų laikas: {guessTimer} s</p>

	<div class="room-settings">
		<h3>Kambario nustatymai</h3>
		<p>Round Length: {roundLength} s</p>
		<p>Round Count: {roundCount}</p>
		{#if lobbyState.question_collections}
			<h4>Pasirinktos klausimų kolekcijos:</h4>
			<ul>
				{#each lobbyState.question_collections as qc}
					<li>{qc.name}</li>
				{/each}
			</ul>
		{/if}
	</div>

	{#if isHost}
		<div class="host-settings">
			<h3>Nustatymai (Tik vedėjui)</h3>
			<label>
				Round Length (s):
				<input type="number" bind:value={roundLength} min="1" />
			</label>
			<label>
				Round Count:
				<input type="number" bind:value={roundCount} min="1" />
			</label>
			<label>
				Spėjimų laikas (s):
				<input type="number" bind:value={guessTimer} min="1" />
			</label>
			<button class="border" on:click={handleUpdateSettings}>Atnaujinti nustatymus</button>

			<h3>Klausimų kolekcijos</h3>
			{#if availableCollections?.length > 0}
				{#each availableCollections as collection}
					<div>
						<input
							type="checkbox"
							id="qc-{collection.id}"
							value={collection.id}
							bind:group={selectedCollections}
						/>
						<label for="qc-{collection.id}">{collection.name}</label>
					</div>
				{/each}
				<button class="border" on:click={handleUpdateCollections}>Atnaujinti kolekcijas</button>
			{:else}
				<p>Nėra prieinamų klausimų kolekcijų.</p>
			{/if}

			<button class="border" on:click={handleStartGame}>Pradėti žaidimą</button>
		</div>
	{/if}

	<h3>Pasirinkite savo personažą</h3>
	<div>
		<h4>Pasirinkti iš esamų:</h4>
		{#each availableCharacters as char}
			<button on:click={() => handleSelectCharacter(char.id)}>
				{#if char.image}
					<img src={char.image} alt={char.name} width="100" />
				{:else}
					<img src="/fallback_character.jpg" alt="Fallback Character" width="100" />
				{/if}
				<span>{char.name}</span>
			</button>
		{/each}
	</div>

	<div>
		<h4>Sukurti naują personažą:</h4>
		<input type="text" bind:value={newCharacterName} placeholder="Personažo vardas" />
		<textarea bind:value={newCharacterDescription} placeholder="Aprašymas"></textarea>
		<input type="file" bind:this={newCharacterImage} accept="image/*" />
		<button on:click={handleCreateCharacter}>Sukurti ir pasirinkti</button>
	</div>

	<button class="border" on:click={handleLeaveLobby}>Palikti kambarį</button>
</main>
