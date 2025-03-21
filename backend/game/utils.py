# game/utils.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_lobby_update(session):
    channel_layer = get_channel_layer()
    group_name = f'lobby_{session.code}'
    players = []
    host_id = None
    for part in session.participants.all():
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
