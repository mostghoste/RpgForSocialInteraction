# game/utils.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_lobby_update(session):
    channel_layer = get_channel_layer()
    group_name = f'lobby_{session.code}'
    players = []
    for part in session.participants.all():
        if part.user:
            players.append(part.user.username)
        else:
            players.append(part.guest_name if part.guest_name else (f"Guest {part.guest_identifier[:8]}" if part.guest_identifier else "Guest"))
    collections_list = list(session.question_collections.values('id', 'name'))
    data = {
        'code': session.code,
        'players': players,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
        'question_collections': collections_list,
    }
    async_to_sync(channel_layer.group_send)(
        group_name,
        {'type': 'lobby_update', 'data': data}
    )
