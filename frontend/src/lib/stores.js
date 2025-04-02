import { writable, derived } from 'svelte/store';

// This store will hold your complete lobby state.
export const lobbyState = writable({
  status: 'join_create',
  code: null,
  current_round: null, // e.g., { round_number, question, end_time }
  guess_deadline: null,
  my_character: null,  // e.g., { name, image }
});

// Utility function to calculate time left from a given end time.
export function calculateTimeLeft(endTimeStr) {
  const endTime = new Date(endTimeStr);
  const diff = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
  const minutes = Math.floor(diff / 60);
  const seconds = diff % 60;
  return `${minutes} min ${seconds} s`;
}

// Derived store that computes banner data from the lobby state.
export const bannerData = derived(lobbyState, $lobbyState => {
  let timeLeftFormatted = '';
  if ($lobbyState.status === 'in_progress' && $lobbyState.current_round?.end_time) {
    timeLeftFormatted = calculateTimeLeft($lobbyState.current_round.end_time);
  } else if ($lobbyState.status === 'guessing' && $lobbyState.guess_deadline) {
    timeLeftFormatted = calculateTimeLeft($lobbyState.guess_deadline);
  }
  return {
    status: $lobbyState.status,
    code: $lobbyState.code,
    timeLeftFormatted,
    question: $lobbyState.current_round?.question || '',
    characterName: $lobbyState.my_character?.name || '',
    characterImage: $lobbyState.my_character?.image || null,
  };
});
