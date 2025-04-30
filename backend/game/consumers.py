# backend/game/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import GameSession, Participant
from asgiref.sync import sync_to_async
from django.utils import timezone

class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.group_name = f'lobby_{self.room_code}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_initial_state()

    async def send_initial_state(self):
        try:
            session = await sync_to_async(GameSession.objects.get)(code=self.room_code)
        except GameSession.DoesNotExist:
            await self.close()
            return

        participants = await sync_to_async(list)(
            session.participants
                   .all()
                   .order_by('joined_at')
                   .select_related('assigned_character', 'user')
        )

        players = []
        host_id = None
        for part in participants:
            username = (
                part.user.username
                if part.user
                else (part.guest_name or f"Guest {part.guest_identifier[:8]}")
            )

            if part.is_host:
                host_id = part.id

            players.append({
                'id': part.id,
                'username': username,
                'characterSelected': part.assigned_character is not None,
                'is_host': part.is_host,
                'is_npc': part.is_npc,
            })

        collections = await sync_to_async(list)(
            session.question_collections.values('id', 'name')
        )

        data = {
            'code': session.code,
            'players': players,
            'host_id': host_id,
            'status': session.status,
            'round_length': session.round_length,
            'round_count': session.round_count,
            'guess_timer': session.guess_timer,
            'guess_deadline': session.guess_deadline.isoformat() if session.guess_deadline else None,
            'question_collections': collections,
        }
        await self.send(text_data=json.dumps(data))


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            participant_id = data.get('participant_id')
            if participant_id:
                try:
                    participant = await sync_to_async(Participant.objects.get)(id=participant_id)
                    participant.last_seen = timezone.now()
                    await sync_to_async(participant.save)()
                except Participant.DoesNotExist:
                    pass
            return

    async def lobby_update(self, event):
        # All lobby updates (chat, round, general) come through here
        await self.send(text_data=json.dumps(event['data']))
