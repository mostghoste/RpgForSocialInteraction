from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from game.models import GameSession, Participant, Character

class AvailableGuessOptionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('available_guess_options')

        self.session = GameSession.objects.create(code='GUESS1')

        self.user1 = User.objects.create_user(username='u1', password='pw')
        self.part1 = Participant.objects.create(
            user=self.user1, game_session=self.session, is_host=True
        )
        self.user2 = User.objects.create_user(username='u2', password='pw2')
        self.part2 = Participant.objects.create(
            user=self.user2, game_session=self.session, is_host=False
        )

        # participant with no character (should be filtered out)
        self.part3 = Participant.objects.create(
            guest_identifier='g3', guest_name='G3', game_session=self.session
        )

        self.char1 = Character.objects.create(name='Hero1', description='', is_public=True)
        self.char2 = Character.objects.create(name='Hero2', description='', is_public=True)
        self.part1.assigned_character = self.char1
        self.part1.save()
        self.part2.assigned_character = self.char2
        self.part2.save()

    def test_missing_params(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Prašome įvesti kambario kodą, dalyvio ID ir slaptažodį.'
        )

    def test_invalid_code(self):
        resp = self.client.get(self.url, {
            'code': 'WRONG',
            'participant_id': self.part1.id,
            'secret': self.part1.secret
        })
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], 'Kambarys nerastas.')

    def test_wrong_status(self):
        # status is still 'pending' by default
        resp = self.client.get(self.url, {
            'code': self.session.code,
            'participant_id': self.part1.id,
            'secret': self.part1.secret
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Spėjimų pasirinkimai prieinami tik spėjimų fazėje.'
        )

    def test_participant_not_found(self):
        self.session.status = 'guessing'
        self.session.save()
        resp = self.client.get(self.url, {
            'code': self.session.code,
            'participant_id': 9999,
            'secret': 'nope'
        })
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], 'Dalyvis nerastas.')

    def test_wrong_secret(self):
        self.session.status = 'guessing'
        self.session.save()
        resp = self.client.get(self.url, {
            'code': self.session.code,
            'participant_id': self.part1.id,
            'secret': 'bad'
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Netinkamas slaptažodis.')

    def test_successful_options(self):
        self.session.status = 'guessing'
        self.session.save()

        # part1 should get part2's character only
        resp = self.client.get(self.url, {
            'code': self.session.code,
            'participant_id': self.part1.id,
            'secret': self.part1.secret
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        opt = data[0]
        self.assertEqual(opt['character_id'], self.char2.id)
        self.assertEqual(opt['character_name'], self.char2.name)
        self.assertIsNone(opt['character_image'])

        # part2 requests options: should get part1's character only
        resp2 = self.client.get(self.url, {
            'code': self.session.code,
            'participant_id': self.part2.id,
            'secret': self.part2.secret
        })
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(len(data2), 1)
        opt2 = data2[0]
        self.assertEqual(opt2['character_id'], self.char1.id)
        self.assertEqual(opt2['character_name'], self.char1.name)
