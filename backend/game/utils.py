# game/utils.py

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

def broadcast_lobby_update(session):
    channel_layer = get_channel_layer()
    group_name = f'lobby_{session.code}'
    players = []
    host_id = None
    for part in session.participants.all().order_by('joined_at'):
        if part.user:
            username = part.user.username
        else:
            username = part.guest_name if part.guest_name else (f"Guest {part.guest_identifier[:8]}" if part.guest_identifier else "Guest")
        if part.is_host:
            username += " 👑"
            host_id = part.id
        players.append({
            'id': part.id,
            'username': username,
            'characterSelected': part.assigned_character is not None
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