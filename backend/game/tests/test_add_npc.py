# game/tests/test_add_npc.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from game.models import GameSession, Participant, Character

class AddNpcTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('add_npc')
        self.session = GameSession.objects.create(code='NPC1')
        self.user = User.objects.create_user(username='host', password='pw')
        self.host = Participant.objects.create(
            user=self.user,
            game_session=self.session,
            is_host=True
        )

        self.char1 = Character.objects.create(
            name='CharA', description='A', is_public=True
        )
        self.char2 = Character.objects.create(
            name='CharB', description='B', is_public=True
        )

    def test_missing_params(self):
        resp = self.client.post(self.url, data={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Trūksta parametrų.')

    def test_invalid_session_or_secret(self):
        # wrong code
        resp1 = self.client.post(self.url, data={
            'code': 'WRONG',
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp1.status_code, 404)
        self.assertEqual(resp1.json()['error'], 'Neteisingi duomenys.')
        # wrong secret
        resp2 = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': 'bad'
        })
        self.assertEqual(resp2.status_code, 404)
        self.assertEqual(resp2.json()['error'], 'Neteisingi duomenys.')

    def test_non_host_cannot_add(self):
        # make host a non-host participant
        self.host.is_host = False
        self.host.save()
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Tik vedėjas gali pridėti NPC.')

    def test_room_full(self):
        # create 8 active participants
        for i in range(8):
            Participant.objects.create(
                guest_identifier=str(i),
                guest_name=f'G{i}',
                game_session=self.session,
                is_active=True
            )
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Kambarys jau pilnas.')

    def test_no_free_characters(self):
        # Assign both public characters to participants so none remain
        Participant.objects.create(
            guest_identifier='u1',
            guest_name='P1',
            game_session=self.session,
            assigned_character=self.char1,
            is_npc=False
        )
        Participant.objects.create(
            guest_identifier='u2',
            guest_name='P2',
            game_session=self.session,
            assigned_character=self.char2,
            is_npc=False
        )
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Nepavyko pridėti NPC, nes nėra laisvų personažų.'
        )

    def test_successful_add_npc(self):
        # initial npc_sequence is zero
        self.assertEqual(self.session.npc_sequence, 0)

        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        # response contains npc_id and character
        self.assertIn('npc_id', body)
        self.assertIn('character', body)
        char_info = body['character']
        self.assertIn('id', char_info)
        self.assertIn('name', char_info)
        self.assertEqual(char_info['id'], Character.objects.get(name=char_info['name']).id)

        # session.npc_sequence incremented
        self.session.refresh_from_db()
        self.assertEqual(self.session.npc_sequence, 1)

        # the new participant exists
        npc = Participant.objects.get(id=body['npc_id'])
        self.assertTrue(npc.is_npc)
        self.assertTrue(npc.is_active)
        self.assertEqual(npc.assigned_character.id, char_info['id'])
        self.assertEqual(npc.guest_name, 'Robotas #1')

        # add second NPC: name should increment
        resp2 = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp2.status_code, 200)
        body2 = resp2.json()
        npc2 = Participant.objects.get(id=body2['npc_id'])
        self.assertEqual(npc2.guest_name, 'Robotas #2')
