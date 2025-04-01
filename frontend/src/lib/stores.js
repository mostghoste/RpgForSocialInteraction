// src/lib/stores.js
import { writable } from 'svelte/store';

export const gameBannerStore = writable({
  status: 'join_create',   // or 'pending', 'in_progress', 'guessing', 'completed'
  timeLeftFormatted: '',   // e.g. "1 min 03 s"
  question: '',
  characterName: '',
  characterImage: null,
  hasSentMessage: false,   // toggles between large and small banner in 'in_progress'
  code: null,              // room code, if needed
  guessesSubmitted: 0,     // how many guesses this player has made
  guessesNeeded: 0         // how many guesses are needed
});
