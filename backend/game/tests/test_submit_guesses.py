from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from game.models import GameSession, Participant, Character, Guess

class SubmitGuessesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('submit_guesses')

        self.session = GameSession.objects.create(code='SUB1', status='guessing')

        self.user = User.objects.create_user(username='u1', password='pw')
        self.guesser = Participant.objects.create(
            user=self.user, game_session=self.session
        )
        self.other1 = Participant.objects.create(
            guest_identifier='g1', guest_name='G1', game_session=self.session
        )
        self.other2 = Participant.objects.create(
            guest_identifier='g2', guest_name='G2', game_session=self.session
        )
        self.no_char = Participant.objects.create(
            guest_identifier='g3', guest_name='G3', game_session=self.session
        )

        self.char1 = Character.objects.create(name='C1', description='', is_public=True)
        self.char2 = Character.objects.create(name='C2', description='', is_public=True)
        self.char3 = Character.objects.create(name='C3', description='', is_public=True)
        self.guesser.assigned_character = self.char1
        self.guesser.save()
        self.other1.assigned_character = self.char2
        self.other1.save()
        self.other2.assigned_character = self.char3
        self.other2.save()

    def test_missing_parameters(self):
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json()['error'],
            'Neteisingas kambarys arba dalyvio ID.'
        )

    def test_invalid_secret(self):
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': 'wrong',
            'guesses': []
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Netinkamas slaptažodis.')

    def test_not_guessing_phase(self):
        self.session.status = 'pending'
        self.session.save()
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': []
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Šiuo metu negalima pateikti spėjimų (ne spėjimų fazė).'
        )

    def test_deadline_passed(self):
        self.session.guess_deadline = timezone.now() - timedelta(seconds=1)
        self.session.save()
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': []
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Laikas spėjimams pasibaigė.')

    def test_too_many_guesses(self):
        # total participants = 4 => max_guesses = 3
        g = {'guessed_participant_id': self.other1.id, 'guessed_character_id': self.char2.id}
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [g, g, g, g]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Per daug spėjimų.')

    def test_missing_guessed_participant_id(self):
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [{}]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Trūksta guessed_participant_id lauko.')

    def test_self_guess(self):
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {'guessed_participant_id': self.guesser.id, 'guessed_character_id': self.char2.id}
            ]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Negalite spėti savęs.')

    def test_duplicate_guess(self):
        g = {'guessed_participant_id': self.other1.id, 'guessed_character_id': self.char2.id}
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [g, g]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Negalite spėti to paties dalyvio daugiau nei vieną kartą.'
        )

    def test_invalid_target_id_returns(self):
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {'guessed_participant_id': 9999, 'guessed_character_id': self.char2.id}
            ]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], 'Neteisingas guessed_participant_id.')

    def test_missing_guessed_character_id(self):
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {'guessed_participant_id': self.other1.id}
            ]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Trūksta guessed_character_id lauko.')

    def test_character_not_in_session(self):
        other_char = Character.objects.create(name='X', description='', is_public=True)
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {'guessed_participant_id': self.other1.id, 'guessed_character_id': other_char.id}
            ]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Šis personažas nepriklauso šiam kambariui.')

    def test_target_without_character(self):
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {'guessed_participant_id': self.no_char.id, 'guessed_character_id': self.char1.id}
            ]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Šis dalyvis neturi priskirto personažo.')

    def test_successful_guesses(self):
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {'guessed_participant_id': self.other1.id, 'guessed_character_id': self.char2.id},
                {'guessed_participant_id': self.other2.id, 'guessed_character_id': self.char3.id}
            ]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body['message'], 'Spėjimai sėkmingai pateikti.')
        updated = body['guesses_updated']
        self.assertEqual(len(updated), 2)
        # verify records exist and correctness
        self.assertTrue(all(Guess.objects.filter(id=g).exists() for g in updated))
        g1 = Guess.objects.get(guesser=self.guesser, guessed_participant=self.other1)
        self.assertTrue(g1.is_correct)
        g2 = Guess.objects.get(guesser=self.guesser, guessed_participant=self.other2)
        self.assertTrue(g2.is_correct)

    def test_incorrect_guess(self):
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {
                    'guessed_participant_id': self.other1.id,
                    'guessed_character_id': self.char3.id
                }
            ]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 200)
        guess = Guess.objects.get(guesser=self.guesser, guessed_participant=self.other1)
        self.assertFalse(guess.is_correct)

    def test_guessing_npc_character_any_npc(self):
        # Create two NPCs with different assigned characters
        npc1 = Participant.objects.create(
            guest_identifier='npc1',
            guest_name='NPC1',
            game_session=self.session,
            is_npc=True
        )
        npc1.assigned_character = self.char2
        npc1.save()

        npc2 = Participant.objects.create(
            guest_identifier='npc2',
            guest_name='NPC2',
            game_session=self.session,
            is_npc=True
        )
        npc2.assigned_character = self.char3
        npc2.save()

        # guess that NPC2 had char2
        payload = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {
                    'guessed_participant_id': npc2.id,
                    'guessed_character_id': self.char2.id
                }
            ]
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, 200)

        # Guess should be marked correct because SOME NPC (npc1) has that character
        guess = Guess.objects.get(guesser=self.guesser, guessed_participant=npc2)
        self.assertTrue(guess.is_correct)

    def test_updating_existing_guess_overwrites(self):
        # guess other1 correctly
        payload1 = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {
                    'guessed_participant_id': self.other1.id,
                    'guessed_character_id': self.char2.id
                }
            ]
        }
        resp1 = self.client.post(self.url, payload1, format='json')
        self.assertEqual(resp1.status_code, 200)
        ids1 = resp1.json()['guesses_updated']
        self.assertEqual(len(ids1), 1)
        guess_obj = Guess.objects.get(id=ids1[0])
        self.assertTrue(guess_obj.is_correct)

        # submit again for the same target but wrong character
        payload2 = {
            'code': self.session.code,
            'participant_id': self.guesser.id,
            'secret': self.guesser.secret,
            'guesses': [
                {
                    'guessed_participant_id': self.other1.id,
                    'guessed_character_id': self.char3.id
                }
            ]
        }
        resp2 = self.client.post(self.url, payload2, format='json')
        self.assertEqual(resp2.status_code, 200)
        ids2 = resp2.json()['guesses_updated']
        # should return the same Guess id
        self.assertEqual(ids1, ids2)
        updated = Guess.objects.get(id=ids2[0])
        self.assertFalse(updated.is_correct)