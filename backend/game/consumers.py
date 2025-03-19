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

        # Build the players list
        participants = await sync_to_async(list)(session.participants.all())
        players = []
        for part in participants:
            if part.user:
                players.append(part.user.username)
            else:
                players.append(
                    part.guest_name if part.guest_name
                    else (f"Guest {part.guest_identifier[:8]}" if part.guest_identifier else "Guest")
                )
        # Wrap the collections query with sync_to_async.
        collections = await sync_to_async(list)(session.question_collections.values('id', 'name'))
        data = {
            'code': session.code,
            'players': players,
            'status': session.status,
            'round_length': session.round_length,
            'round_count': session.round_count,
            'question_collections': collections,
        }
        await self.send(text_data=json.dumps(data))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def lobby_update(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))

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
                    print("ERROR: Couldn't find the participant to update.")
            return