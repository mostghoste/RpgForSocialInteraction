# backend/game/tests/test_start_game.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse

from django.contrib.auth.models import User
from game.models import (
    GameSession, Participant, Character,
    QuestionCollection, Question, Round
)

class StartGameTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('start_game')

        self.user = User.objects.create_user(username='host', password='pw')
        self.session = GameSession.objects.create(code='ROOM01')

        self.host = Participant.objects.create(
            user=self.user,
            game_session=self.session,
            is_host=True
        )

        self.guest = Participant.objects.create(
            guest_identifier='g1',
            guest_name='Guest1',
            game_session=self.session,
            is_host=False
        )

        self.guest2 = Participant.objects.create(
            guest_identifier='g2',
            guest_name='Guest2',
            game_session=self.session,
            is_host=False
        )

        # Assign public characters to host and guests
        for p in [self.host, self.guest, self.guest2]:
            c = Character.objects.create(name=f"{p.id}-char", is_public=True)
            p.assigned_character = c
            p.save()

    def test_missing_parameters(self):
        resp = self.client.post(self.url, data={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Kambario kodas, dalyvio ID ir slaptažodis privalomi.'
        )

    def test_invalid_room_or_participant(self):
        # wrong code
        resp = self.client.post(self.url, {
            'code': 'BAD',
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 404)
        self.assertIn('Neteisingas kambarys', resp.json()['error'])

        # wrong participant
        resp = self.client.post(self.url, {
            'code': self.session.code,
            'participant_id': 9999,
            'secret': 'nope'
        })
        self.assertEqual(resp.status_code, 404)
        self.assertIn('Neteisingas kambarys', resp.json()['error'])

    def test_wrong_secret(self):
        resp = self.client.post(self.url, {
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': 'wrong'
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Netinkamas slaptažodis.')

    def test_non_host_cannot_start(self):
        resp = self.client.post(self.url, {
            'code': self.session.code,
            'participant_id': self.guest.id,
            'secret': self.guest.secret
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Tik vedėjas gali pradėti žaidimą.')

    def test_already_started(self):
        self.session.status = 'in_progress'
        self.session.save()
        resp = self.client.post(self.url, {
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Žaidimas jau prasidėjo arba baigėsi.'
        )

    def test_not_enough_total_participants(self):
        # remove one guest so only 2 participants remain
        self.guest2.delete()
        resp = self.client.post(self.url, {
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Žaidimui reikia bent 3 dalyvių.'
        )

    def test_not_enough_humans(self):
        # make both guests into NPCs
        self.guest.is_npc = True
        self.guest.save()
        self.guest2.is_npc = True
        self.guest2.save()

        # Add a collection with enough questions
        qc = QuestionCollection.objects.create(name='QC_for_humans_test')
        for i in range(self.session.round_count):
            q = Question.objects.create(text=f"Q{i}", creator=self.user)
            qc.questions.add(q)
        self.session.question_collections.add(qc)

        resp = self.client.post(self.url, {
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Žaidimui reikia bent 2 žmonių.'
        )

    def test_unassigned_character(self):
        # remove character from one participant
        self.guest2.assigned_character = None
        self.guest2.save()
        resp = self.client.post(self.url, {
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Kiekvienas dalyvis privalo turėti personažą.'
        )

    def test_not_enough_questions(self):
        # no collections at all
        resp = self.client.post(self.url, {
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Klausimų kolekcijose nepakanka klausimų pagal nurodytą raundų skaičių.'
        )

    def test_successful_start(self):
        # Set up questions
        qc = QuestionCollection.objects.create(name='QC1')
        self.session.round_count = 2
        self.session.save()
        for i in range(2):
            q = Question.objects.create(text=f"Q{i}", creator=self.user)
            qc.questions.add(q)
        self.session.question_collections.add(qc)

        resp = self.client.post(self.url, {
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['message'], 'Žaidimas pradėtas.')
        self.assertEqual(data['code'], self.session.code)
        self.assertEqual(data['status'], 'in_progress')
        self.assertEqual(data['round_count'], 2)
        # Check current_round payload
        cr = data['current_round']
        self.assertEqual(cr['round_number'], 1)
        self.assertIn(cr['question'], ['Q0', 'Q1'])
        self.assertTrue(cr['end_time'].endswith('Z') or '+' in cr['end_time'])

        rounds = Round.objects.filter(game_session=self.session)
        self.assertEqual(rounds.count(), 1)
        self.assertEqual(rounds.first().round_number, 1)
