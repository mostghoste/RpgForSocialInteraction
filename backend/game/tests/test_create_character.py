# backend/game/tests/test_create_character.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from game.models import GameSession, Participant, Character

class CreateCharacterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('create_character')

        self.user = User.objects.create_user(username='host', password='pw')
        self.session = GameSession.objects.create(code='ROOM03')

        self.participant = Participant.objects.create(
            user=self.user,
            game_session=self.session,
            is_host=True
        )
        self.guest = Participant.objects.create(
            guest_identifier='g2',
            guest_name='Guest',
            game_session=self.session,
            is_host=False
        )

    def test_missing_parameters(self):
        resp = self.client.post(self.url, data={}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Trūksta privalomų parametrų.')

    def test_invalid_room_or_participant(self):
        data = {
            'code': 'BADCODE',
            'participant_id': 9999,
            'secret': 'nope',
            'name': 'NewChar'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json()['error'],
            'Neteisingas kambario kodas arba dalyvio ID.'
        )

    def test_not_pending_status(self):
        self.session.status = 'in_progress'
        self.session.save()

        data = {
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'name': 'NewChar'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Negalima keisti personažų, kai žaidimas jau prasidėjo.'
        )

    def test_wrong_secret(self):
        data = {
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': 'wrong',
            'name': 'NewChar'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Netinkas slaptažodis.')

    def test_invalid_file_type(self):
        txt = SimpleUploadedFile('test.txt', b'hello', content_type='text/plain')
        data = {
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'name': 'WithBadFile',
        }
        resp = self.client.post(self.url, data={**data, 'image': txt})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Neteisingas failo tipas. Tinka .jpg, .png.'
        )

    def test_too_large_file(self):
        # create a 5MB+1 byte JPEG
        large = SimpleUploadedFile(
            'big.jpg',
            b'a' * (5 * 1024 * 1024 + 1),
            content_type='image/jpeg'
        )
        data = {
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'name': 'WithLargeFile',
        }
        resp = self.client.post(self.url, data={**data, 'image': large})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Paveikslėlis per didelis. Didžiausias leidžiamas dydis yra 5MB.'
        )

    def test_success_without_image_guest(self):
        data = {
            'code': self.session.code,
            'participant_id': self.guest.id,
            'secret': self.guest.secret,
            'name': 'GuestChar',
            'description': 'GuestDesc'
        }
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload['message'], 'Personažas sukurtas ir pasirinktas.')
        char_id = payload['character_id']

        char = Character.objects.get(id=char_id)
        self.assertEqual(char.name, 'GuestChar')
        self.assertEqual(char.description, 'GuestDesc')
        self.assertIsNone(char.creator)

        # participant should now have that character assigned
        self.guest.refresh_from_db()
        self.assertEqual(self.guest.assigned_character_id, char_id)

    def test_success_with_image_and_authenticated(self):
        # authenticate client
        self.client.force_authenticate(self.user)
        img = SimpleUploadedFile(
            'avatar.png',
            b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
            content_type='image/png'
        )
        data = {
            'code': self.session.code,
            'participant_id': self.participant.id,
            'secret': self.participant.secret,
            'name': 'UserChar',
            'description': 'UserDesc',
        }
        resp = self.client.post(self.url, data={**data, 'image': img})
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload['message'], 'Personažas sukurtas ir pasirinktas.')
        char_id = payload['character_id']

        char = Character.objects.get(id=char_id)
        self.assertEqual(char.name, 'UserChar')
        self.assertEqual(char.description, 'UserDesc')
        self.assertEqual(char.creator_id, self.user.id)
        self.assertTrue(char.image.name)  # image path set

        # and participant assigned
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.assigned_character_id, char_id)
