# backend/game/tests/test_join_room.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from game.models import GameSession, Participant, QuestionCollection, Round, Question


class JoinRoomTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='host', password='pw')

        self.session = GameSession.objects.create(code='AAAAAA')

        # one public and one user-owned collection
        QuestionCollection.objects.create(name='public', created_by=None)
        QuestionCollection.objects.create(name='private', created_by=self.user)

    def test_missing_code(self):
        url = reverse('join_room')
        resp = self.client.post(url, data={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Kambario kodas privalomas.')

    def test_invalid_code(self):
        url = reverse('join_room')
        resp = self.client.post(url, data={'code': 'TESTINGSUX'})
        self.assertEqual(resp.status_code, 404)
        self.assertIn('neegzistuoja', resp.json()['error'])

    def test_guest_join_missing_username(self):
        url = reverse('join_room')
        resp = self.client.post(url, data={'code': self.session.code})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Prašome įvesti vartotojo vardą.')

    def test_guest_join_duplicate_username(self):
        # first guest
        Participant.objects.create(
            guest_identifier='1234',
            guest_name='Alice',
            game_session=self.session,
            is_host=True
        )
        url = reverse('join_room')
        resp = self.client.post(url, data={
            'code': self.session.code,
            'guest_username': 'Alice'
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('jau naudojamas', resp.json()['error'])

    def test_guest_join_success_assigns_public_collections_and_host(self):
        url = reverse('join_room')
        resp = self.client.post(url, data={
            'code': self.session.code,
            'guest_username': 'Bob'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # participant fields
        self.assertIn('participant_id', data)
        self.assertIn('secret', data)
        self.assertTrue(data['is_host'])  # first join is host

        # only the public collections should be assigned
        cols = {c['name'] for c in data['question_collections']}
        self.assertEqual(cols, {'public'})

        # DB check
        p = Participant.objects.get(id=data['participant_id'])
        self.assertEqual(p.guest_name, 'Bob')
        self.assertTrue(p.is_host)

    def test_authenticated_auto_join_success(self):
        self.client.force_authenticate(self.user)
        url = reverse('join_room')
        resp = self.client.post(url, data={'code': self.session.code})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # participant fields
        self.assertIn('participant_id', data)
        self.assertIn('secret', data)
        self.assertTrue(data['is_host'])

        # collections should include both public and private
        names = {c['name'] for c in data['question_collections']}
        self.assertSetEqual(names, {'public', 'private'})

    def test_reconnect_with_wrong_secret(self):
        # first we join as guest
        join = self.client.post(reverse('join_room'),
                                {'code': self.session.code, 'guest_username': 'Cathy'})
        pid = join.json()['participant_id']
        # now attempt reconnect with bad secret
        resp = self.client.post(reverse('join_room'),
                                {'code': self.session.code,
                                 'participant_id': pid,
                                 'secret': 'wrongsecret'})
        self.assertEqual(resp.status_code, 403)
        self.assertIn('slaptažodis', resp.json()['error'])

    def test_reconnect_nonexistent_participant(self):
        resp = self.client.post(reverse('join_room'),
                                {'code': self.session.code,
                                 'participant_id': 9999,
                                 'secret': 'anything'})
        self.assertEqual(resp.status_code, 404)
        self.assertIn('Dalyvis nerastas', resp.json()['error'])

    def test_reconnect_success_returns_same_participant(self):
        # join once
        join = self.client.post(reverse('join_room'),
                                {'code': self.session.code,
                                 'guest_username': 'Dave'})
        data1 = join.json()
        # reconnect
        resp = self.client.post(reverse('join_room'),
                                {'code': self.session.code,
                                 'participant_id': data1['participant_id'],
                                 'secret': data1['secret']})
        self.assertEqual(resp.status_code, 200)
        data2 = resp.json()
        self.assertEqual(data2['participant_id'], data1['participant_id'])
        self.assertEqual(data2['secret'], data1['secret'])

    def test_room_full_for_guest(self):
        # create 8 active participants
        for i in range(8):
            Participant.objects.create(
                guest_identifier=str(i),
                guest_name=f'G{i}',
                game_session=self.session,
                is_active=True
            )
        url = reverse('join_room')
        resp = self.client.post(url, data={
            'code': self.session.code,
            'guest_username': 'NewGuy'
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('pilnas', resp.json()['error'])

    def test_room_not_pending_for_guest(self):
        # mark session as in_progress
        self.session.status = 'in_progress'
        self.session.save()
        url = reverse('join_room')
        resp = self.client.post(url, data={
            'code': self.session.code,
            'guest_username': 'Erin'
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('prasidėjo', resp.json()['error'])

    def test_authenticated_join_full_room(self):
        # fill up the room with 8 other guests
        for i in range(8):
            Participant.objects.create(
                guest_identifier=str(i),
                guest_name=f'Guest{i}',
                game_session=self.session,
                is_active=True
            )

        # authenticate and attempt to join
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            reverse('join_room'),
            data={'code': self.session.code}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('pilnas', resp.json()['error'])

    def test_reconnect_in_progress(self):
        join = self.client.post(
            reverse('join_room'),
            {'code': self.session.code, 'guest_username': 'ReconnectGuy'}
        )
        data = join.json()
        pid = data['participant_id']
        secret = data['secret']

        # Create a question and round that is still ongoing
        q = Question.objects.create(text='What is 2+2?', creator=self.user)
        now = timezone.now()
        rnd = Round.objects.create(
            game_session=self.session,
            question=q,
            round_number=1,
            start_time=now,
            end_time=now + timedelta(seconds=300)
        )

        self.session.status = 'in_progress'
        self.session.save()

        # now reconnect
        resp = self.client.post(
            reverse('join_room'),
            {
                'code': self.session.code,
                'participant_id': pid,
                'secret': secret
            }
        )
        self.assertEqual(resp.status_code, 200)
        data2 = resp.json()

        # confirm its the same participant
        self.assertEqual(data2['participant_id'], pid)
        self.assertEqual(data2['secret'], secret)

        # current_round is set correctly
        self.assertIn('current_round', data2)
        cr = data2['current_round']
        self.assertEqual(cr['round_number'], rnd.round_number)
        self.assertEqual(cr['question'], q.text)
        self.assertTrue(cr['end_time'].startswith((rnd.end_time).isoformat()[:19]))
