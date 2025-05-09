from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from game.models import GameSession, Participant, Round, Message, Question
import game.api_views as views

class SendChatMessageTests(TestCase):
    def setUp(self):
        # Silence broadcast function
        views.broadcast_chat_message = lambda *args, **kwargs: None

        self.client = APIClient()
        self.url = reverse('send_chat_message')

        self.session = GameSession.objects.create(code='CHAT1')

        self.user = User.objects.create_user(username='u1', password='pw')
        self.participant = Participant.objects.create(
            user=self.user,
            game_session=self.session,
            is_host=True
        )
        self.guest = Participant.objects.create(
            guest_identifier='g1',
            guest_name='Guest',
            game_session=self.session,
            is_host=False
        )

        self.session.status = 'in_progress'
        self.session.save()

        q = Question.objects.create(text='dummy?', creator=self.user)

        # Create a live round that ends in the future
        self.current_round = Round.objects.create(
            game_session=self.session,
            question=q,
            round_number=1,
            start_time=timezone.now() - timedelta(seconds=5),
            end_time=timezone.now() + timedelta(seconds=300)
        )

    def test_missing_fields(self):
        resp = self.client.post(self.url, data={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Trūksta reikiamų laukų.')

    def test_invalid_session(self):
        data = {
            'code': 'WRONG',
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'text': 'hello'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], 'Nerasta žaidimo sesija.')

    def test_not_in_progress(self):
        self.session.status = 'pending'
        self.session.save()

        data = {
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'text': 'hello'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Šios žaidimo stadijos metu žinučių siųsti negalima.'
        )

    def test_participant_not_found(self):
        data = {
            'code': self.session.code,
            'participant_id': 9999,
            'secret': 'whatever',
            'text': 'hi'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], 'Dalyvis nerastas.')

    def test_wrong_secret(self):
        data = {
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': 'badsecret',
            'text': 'hi'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Netinkamas slaptažodis.')

    def test_no_current_round(self):
        # expire the only round
        self.current_round.end_time = timezone.now() - timedelta(seconds=1)
        self.current_round.save()

        data = {
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'text': 'late'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Palaukite sekančio raundo.')

    def test_successful_send(self):
        data = {
            'code': self.session.code,
            'participant_id': self.guest.id,
            'secret': self.guest.secret,
            'text': 'Hello everyone!'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'Žinutė išsiųsta.'})

        # Check that the Message was created
        msgs = Message.objects.filter(round=self.current_round, participant=self.guest)
        self.assertEqual(msgs.count(), 1)
        self.assertEqual(msgs.first().text, 'Hello everyone!')
