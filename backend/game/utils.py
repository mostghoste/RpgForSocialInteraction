# game/utils.py

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import GameSession

def broadcast_lobby_update(session: GameSession):
    channel_layer = get_channel_layer()
    group_name = f'lobby_{session.code}'
    players = list(session.participants.values_list('user__username', flat=True))
    players = [p if p is not None else "Guest" for p in players]
    data = {
        'code': session.code,
        'players': players,
        'status': session.status,
    }
    async_to_sync(channel_layer.group_send)(
        group_name,
        {'type': 'lobby_update', 'data': data}
    )
