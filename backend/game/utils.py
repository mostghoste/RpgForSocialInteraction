# game/utils.py

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import GameSession

def broadcast_lobby_update(session: GameSession):
    channel_layer = get_channel_layer()
    group_name = f'lobby_{session.code}'
    players_qs = session.participants.values_list('user__username', flat=True)
    players = [username if username is not None else "Guest" for username in players_qs]
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
