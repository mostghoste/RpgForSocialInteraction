# game/utils.py

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import GameSession

def broadcast_lobby_update(session: GameSession):
    channel_layer = get_channel_layer()
    group_name = f'lobby_{session.code}'
    players = []
    for part in session.participants.all():
        if part.user:
            players.append(part.user.username)
        else:
            players.append(part.guest_name if part.guest_name else (f"Guest {part.guest_identifier[:8]}" if part.guest_identifier else "Guest"))
    data = {
        'code': session.code,
        'players': players,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
    }
    async_to_sync(channel_layer.group_send)(
        group_name,
        {'type': 'lobby_update', 'data': data}
    )

