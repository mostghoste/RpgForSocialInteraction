# game/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import GameSession, Participant
from asgiref.sync import sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'chat'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')

        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))

class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.group_name = f'lobby_{self.room_code}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # Send current state after connecting
        await self.send_initial_state()

    async def send_initial_state(self):
        try:
            session = await sync_to_async(GameSession.objects.get)(code=self.room_code)
        except GameSession.DoesNotExist:
            await self.close()
            return
        players_qs = await sync_to_async(list)(
            session.participants.values_list('user__username', flat=True)
        )
        players = [p if p is not None else "Guest" for p in players_qs]
        data = {
            'code': session.code,
            'players': players,
            'status': session.status,
            'round_length': session.round_length,
            'round_count': session.round_count,
        }
        await self.send(text_data=json.dumps(data))

    async def disconnect(self):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # This method will be called when the group sends an update
    async def lobby_update(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            # Participant id gets passed from the frontend
            participant_id = data.get('participant_id')
            if participant_id:
                try:
                    participant = await sync_to_async(Participant.objects.get)(id=participant_id)
                    participant.last_seen = timezone.now()
                    await sync_to_async(participant.save)()
                except Participant.DoesNotExist:
                    print("ERROR: Couldn't find the participant to update.")
                    pass
            return
