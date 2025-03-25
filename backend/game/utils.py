# game/utils.py

import random
from datetime import timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from .models import GameSession, Round

def broadcast_lobby_update(session):
    channel_layer = get_channel_layer()
    group_name = f'lobby_{session.code}'

    players = []
    host_id = None
    for part in session.participants.all().order_by('joined_at'):
        if part.is_host:
            host_id = part.id
        players.append({
            'id': part.id,
            'username': part.user.username if part.user else (part.guest_name or f"Guest {part.guest_identifier[:8]}"),
            'characterSelected': part.assigned_character is not None,
            'is_host': part.is_host,
        })

    collections_list = list(session.question_collections.values('id', 'name'))

    data = {
        'code': session.code,
        'players': players,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
        'guess_timer': session.guess_timer,
        'guess_deadline': session.guess_deadline.isoformat() if session.guess_deadline else None,
        'question_collections': collections_list,
        'host_id': host_id,
    }
    async_to_sync(channel_layer.group_send)(
        group_name,
        {'type': 'lobby_update', 'data': data}
    )


def broadcast_chat_message(room_code, message_obj):
    channel_layer = get_channel_layer()
    participant = message_obj.participant
    character = participant.assigned_character

    data = {
        'type': 'chat_update',
        'message': {
            'id': message_obj.id,
            'text': message_obj.text,
            'sentAt': message_obj.sent_at.isoformat(),
            'characterName': character.name if character else '???',
            'characterImage': character.image.url if (character and character.image) else None
        }
    }

    async_to_sync(channel_layer.group_send)(
        f'lobby_{room_code}',
        {
            'type': 'lobby_update',
            'data': data
        }
    )

def broadcast_round_update(room_code, round_obj):
    channel_layer = get_channel_layer()
    data = {
         'type': 'round_update',
         'round': {
              'round_number': round_obj.round_number,
              'question': round_obj.question.text if round_obj.question else '',
              'end_time': round_obj.end_time.isoformat(),
         }
    }
    async_to_sync(channel_layer.group_send)(
         f'lobby_{room_code}',
         {'type': 'lobby_update', 'data': data}
    )

def check_and_advance_rounds():
    print("⏰ Checking in-progress sessions...")
    now = timezone.now()
    sessions = GameSession.objects.filter(status='in_progress')

    for session in sessions:
        latest_round = (
            Round.objects
            .filter(game_session=session)
            .order_by('-round_number')
            .first()
        )
        # First round is created when host starts the game so this is redundant
        if not latest_round:
            print(f"🆕 No rounds yet for session {session.code}. Starting round 1.")
            next_round_number = 1
        else:
            if latest_round.end_time > now:
                print(f"⏳ Round {latest_round.round_number} in session {session.code} is still ongoing.")
                continue
            next_round_number = latest_round.round_number + 1

        if next_round_number > session.round_count:
            print(f"✅ Session {session.code} finished all rounds. Moving to 'guessing'.")
            session.status = 'guessing'
            session.guess_deadline = now + timedelta(seconds=session.guess_timer)
            session.save()
            broadcast_lobby_update(session)
            continue

        collections = list(session.question_collections.all())
        question = None
        if collections:
            collection = random.choice(collections)
            questions = list(collection.questions.exclude(round__game_session=session))
            if questions:
                question = random.choice(questions)
        end_time = now + timedelta(seconds=session.round_length)
        new_round = Round.objects.create(
            game_session=session,
            question=question,
            round_number=next_round_number,
            end_time=end_time
        )
        print(f"🌀 Created round {next_round_number} in session {session.code}")
        broadcast_round_update(session.code, new_round)
        broadcast_lobby_update(session)
