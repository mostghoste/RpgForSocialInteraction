# backend/game/tests/test_update_question_collections.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from game.models import GameSession, Participant, QuestionCollection

class UpdateQuestionCollectionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.host_user = User.objects.create_user(username='host', password='pw')
        self.other_user = User.objects.create_user(username='other', password='pw')

        self.session = GameSession.objects.create(code='ROOM01')
        self.host_participant = Participant.objects.create(
            user=self.host_user,
            game_session=self.session,
            is_host=True
        )

        self.public_coll = QuestionCollection.objects.create(
            name='Public', created_by=None
        )
        self.host_coll = QuestionCollection.objects.create(
            name='HostOnly', created_by=self.host_user
        )
        self.other_coll = QuestionCollection.objects.create(
            name='OtherUser', created_by=self.other_user
        )

        self.url = reverse('update_question_collections')

    def test_missing_parameters(self):
        resp = self.client.post(self.url, data={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Kambario kodas, dalyvio ID ir slaptažodis privalomi.'
        )

    def test_invalid_room_or_participant(self):
        resp = self.client.post(self.url, data={
            'code': 'INVALID',
            'participant_id': 9999,
            'secret': 'nope'
        })
        self.assertEqual(resp.status_code, 404)
        self.assertIn('Neteisingas kambarys arba dalyvio ID', resp.json()['error'])

    def test_wrong_secret(self):
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host_participant.id,
            'secret': 'wrong'
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Netinkamas slaptažodis.')

    def test_non_host_forbidden(self):
        # create a non-host participant
        guest = Participant.objects.create(
            guest_identifier='guest1',
            guest_name='Guest',
            game_session=self.session,
            is_host=False
        )
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': guest.id,
            'secret': guest.secret,
            'collections': [self.public_coll.id]
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Tik vedėjas gali keisti klausimų kolekcijas.')

    def test_not_pending_status(self):
        self.session.status = 'in_progress'
        self.session.save()
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host_participant.id,
            'secret': self.host_participant.secret,
            'collections': [self.public_coll.id]
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Negalima keisti klausimų kolekcijų, kai žaidimas jau prasidėjo.'
        )

    def test_successful_update(self):
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host_participant.id,
            'secret': self.host_participant.secret,
            'collections': [self.public_coll.id, self.host_coll.id]
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        returned_ids = {c['id'] for c in data['question_collections']}
        self.assertSetEqual(returned_ids, {self.public_coll.id, self.host_coll.id})

    def test_invalid_collection_selection_raises_error(self):
        # include a non-existent collection ID
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host_participant.id,
            'secret': self.host_participant.secret,
            'collections': [9999]
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Pasirinktos neteisingos klausimų kolekcijos.'
        )

    def test_cannot_select_other_users_collection(self):
        # attempt to select a collection owned by another user
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host_participant.id,
            'secret': self.host_participant.secret,
            'collections': [self.other_coll.id]
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Pasirinktos neteisingos klausimų kolekcijos.'
        )

    def test_guest_host_can_select_only_public(self):
        guest_host = Participant.objects.create(
            guest_identifier='guest-host-1',
            guest_name='GuestHost',
            game_session=self.session,
            is_host=True
        )

        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': guest_host.id,
            'secret': guest_host.secret,
            'collections': [self.public_coll.id]
        }, format='json')
        self.assertEqual(resp.status_code, 200)

        returned = {c['id'] for c in resp.json()['question_collections']}
        self.assertSetEqual(returned, {self.public_coll.id})

    def test_guest_host_cannot_select_nonpublic(self):
        guest_host = Participant.objects.create(
            guest_identifier='guest-host-2',
            guest_name='GuestHost2',
            game_session=self.session,
            is_host=True
        )

        # attempt to select the host_user's own collection
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': guest_host.id,
            'secret': guest_host.secret,
            'collections': [self.host_coll.id]
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Pasirinktos neteisingos klausimų kolekcijos.'
        )
