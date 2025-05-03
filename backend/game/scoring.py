# backend/game/scoring.py

from django.db.models import Q
from .models import Round, Guess

def compute_score_breakdown(participant):
    session = participant.game_session
    breakdown = []

    # Points for sending a chat message in each round
    rounds_with_msgs = (
        Round.objects
             .filter(game_session=session, messages__participant=participant)
             .distinct()
    )
    for rnd in rounds_with_msgs:
        breakdown.append({
            'description': f'už atsakymą {rnd.round_number} raunde',
            'points': 50
        })

    # Points for each correct guess you made
    correct_guesses = Guess.objects.filter(guesser=participant, is_correct=True)
    for guess in correct_guesses:
        if guess.guessed_participant and guess.guessed_participant.is_npc:
            breakdown.append({
                'description': f'už teisingai atpažintą robotą „{guess.guessed_character.name}“',
                'points': 50
            })
        else:
            target = guess.guessed_participant
            target_name = target.user.username if target.user else target.guest_name
            breakdown.append({
                'description': f'už teisingai atpažintą žaidėją {target_name}',
                'points': 100
            })


    # Points for being guessed by others
        # If nobody guessed you - 0
        # If everyone guessed you - 0
        # Otherwise, +50 per person who guessed you correctly
    human_guessers = session.participants.filter(
        is_active=True, is_npc=False
    ).exclude(id=participant.id)
    total_humans = human_guessers.count()

    correct_received = Guess.objects.filter(
        guessed_participant=participant, is_correct=True
    )
    correct_count = correct_received.count()

    if correct_count == 0:
        # nobody guessed you
        breakdown.append({
            'description': 'už tai, kad niekas neatspėjo tavo personažo',
            'points': 0
        })
    elif correct_count == total_humans and total_humans > 0:
        # everyone guessed you
        breakdown.append({
            'description': 'už tai, kad visi atspėjo tavo personažą',
            'points': 0
        })
    else:
        # some—but not all—guessed you
        for guess in correct_received:
            g = guess.guesser
            g_name = g.user.username if g.user else g.guest_name
            breakdown.append({
                'description': f'už tai, kad {g_name} atspėjo tavo personažą',
                'points': 50
            })

    total = sum(item['points'] for item in breakdown)
    return breakdown, total
