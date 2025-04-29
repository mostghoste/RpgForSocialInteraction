# backend/game/scoring.py

from django.db.models import Count, Q
from .models import Round, Guess

def compute_score_breakdown(participant):
    session = participant.game_session
    breakdown = []

    # 100 points per round where >=1 message is sent
    rounds_with_msgs = (
        Round.objects
             .filter(game_session=session, messages__participant=participant)
             .distinct()
    )
    for rnd in rounds_with_msgs:
        breakdown.append({
            'description': f'+100 už atsakymą {rnd.round_number} raunde',
            'points': 100
        })

    # 50 points per correct guess made
    correct_guesses = Guess.objects.filter(guesser=participant, is_correct=True)
    for guess in correct_guesses:
        gp = guess.guessed_participant
        guessed_name = gp.user.username if gp.user else gp.guest_name
        breakdown.append({
            'description': f'+50 už teisingai atpažintą {guessed_name}',
            'points': 50
        })

    total = sum(item['points'] for item in breakdown)
    return breakdown, total
