# game/utils.py

import random
from datetime import timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from .models import Round

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
            'type': 'lobby_update',  # Re-using the same handler in LobbyConsumer
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
    print("⏰ Checking rounds...")
    now = timezone.now()
    ongoing_rounds = Round.objects.filter(end_time__lte=now, game_session__status='in_progress')

    for r in ongoing_rounds:
        session = r.game_session
        total_rounds = session.round_count
        current_round_number = r.round_number

        if current_round_number >= total_rounds:
            session.status = 'guessing'
            session.save()
            broadcast_lobby_update(session)
            continue

        # Create the next round
        next_round_number = current_round_number + 1
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

        broadcast_round_update(session.code, new_round)
        broadcast_lobby_update(session)