# backend/game/tests/test_select_character.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from game.models import GameSession, Participant, Character

class SelectCharacterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('select_character')

        self.user = User.objects.create_user(username='host', password='pw')
        self.session = GameSession.objects.create(code='ROOM02')

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

        self.char1 = Character.objects.create(name='Alice', description='Desc1', is_public=True)
        self.char2 = Character.objects.create(name='Bob',   description='Desc2', is_public=True)

    def test_missing_parameters(self):
        resp = self.client.post(self.url, data={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Trūksta privalomų parametrų.')

    def test_invalid_room_or_participant(self):
        # wrong code
        resp = self.client.post(self.url, data={
            'code': 'WRONG',
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'character_id': self.char1.id
        })
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json()['error'],
            'Neteisingas kambario kodas arba dalyvio ID.'
        )

        # wrong participant
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': 9999,
            'secret': 'nope',
            'character_id': self.char1.id
        })
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json()['error'],
            'Neteisingas kambario kodas arba dalyvio ID.'
        )

    def test_cannot_change_after_start(self):
        self.session.status = 'in_progress'
        self.session.save()

        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'character_id': self.char1.id
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Negalima keisti personažų, kai žaidimas jau prasidėjo.'
        )

    def test_wrong_secret(self):
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': 'wrongsecret',
            'character_id': self.char1.id
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Neteisingas slaptažodis.')

    def test_character_not_found(self):
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'character_id': 9999
        })
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], 'Personažas nerastas.')

    def test_cannot_select_already_taken(self):
        # assign char1 to guest first
        self.guest.assigned_character = self.char1
        self.guest.save()

        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'character_id': self.char1.id
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Šis personažas jau pasirinktas.')

    def test_successful_selection(self):
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'character_id': self.char2.id
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'Personažas pasirinktas.'})

        self.participant.refresh_from_db()
        self.assertEqual(self.participant.assigned_character, self.char2)
        
    def test_guest_cannot_select_user_private(self):
        # guest participant tries to pick a user1 created private char
        private = Character.objects.create(
            name='PrivateByUser1',
            description='desc',
            is_public=False,
            creator=self.user
        )

        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.guest.id,
            'secret': self.guest.secret,
            'character_id': private.id
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json()['error'],
            'Negalima pasirinkti kito vartotojo personažo.'
        )

    def test_authenticated_user_cannot_select_another_users_private(self):
        # user1 tries to pick user2's private character
        private2 = Character.objects.create(
            name='PrivateByUser2',
            description='desc',
            is_public=False,
            creator=User.objects.create_user(username='user2', password='pw')
        )
        # authenticate as user1
        self.client.force_authenticate(self.user)

        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'character_id': private2.id
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(
            resp.json()['error'],
            'Negalima pasirinkti kito vartotojo personažo.'
        )

    def test_authenticated_user_can_select_own_private(self):
        # user1 picks their own private character
        own_private = Character.objects.create(
            name='User1Private',
            description='desc',
            is_public=False,
            creator=self.user
        )
        # authenticate as user1
        self.client.force_authenticate(self.user)

        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'character_id': own_private.id
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'Personažas pasirinktas.'})
