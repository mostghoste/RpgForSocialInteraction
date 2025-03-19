# game/utils.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_lobby_update(session):
    channel_layer = get_channel_layer()
    group_name = f'lobby_{session.code}'
    players = []
    for part in session.participants.all():
        if part.user:
            username = part.user.username
        elif part.guest_name:
            username = part.guest_name
        elif part.guest_identifier:
            username = f"Guest {part.guest_identifier[:8]}"
        else:
            username = "Guest"
        if part.is_host:
            username += " 👑"
        players.append(username)
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
