# game/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import GameSession
from .utils import check_and_advance_rounds, broadcast_lobby_update

@shared_task
def run_round_check():
    print("⏰ Celery: Checking rounds...")
    check_and_advance_rounds()

@shared_task
def run_game_end_check():
    now = timezone.now()
    # Find sessions in the guessing phase whose deadline has passed
    sessions = GameSession.objects.filter(status='guessing', guess_deadline__lte=now)
    for session in sessions:
        print(f"Ending game for session {session.code}")
        # Calculate results for each participant
        for participant in session.participants.all():
            # Calculate points based on correct guesses
            correct_guess_count = participant.guesses_made.filter(is_correct=True).count()
            points_from_guesses = correct_guess_count * 50
            
            rounds_with_messages = session.rounds.filter(messages__participant=participant).distinct().count()
            points_from_messages = rounds_with_messages * 100
            
            total_points = points_from_guesses + points_from_messages
            participant.points = total_points
            participant.save()
        
        # Change the session status to 'completed'
        session.status = 'completed'
        session.save()
        
        # Broadcast the updated lobby so that clients know the game is over
        broadcast_lobby_update(session)
        
    return "Game end check complete"