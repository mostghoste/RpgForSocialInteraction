# backend/game/tests.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q

from game.models import QuestionCollection, GameSession

class CreateRoomTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password')

        QuestionCollection.objects.create(name='public_collection', created_by=None)
        QuestionCollection.objects.create(name='user_collection', created_by=self.user)

    def test_anonymous_create_room(self):
        url = reverse('create_room')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('code', data)
        self.assertEqual(data['status'], 'pending')

        # should not auto join anonymous user
        self.assertNotIn('participant_id', data)
        self.assertNotIn('secret', data)
        self.assertNotIn('is_host', data)

        code = data['code']
        self.assertEqual(len(code), 6)
        self.assertTrue(GameSession.objects.filter(code=code, status='pending').exists())

    def test_authenticated_create_room(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('create_room')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # participant details present
        self.assertIn('participant_id', data)
        self.assertIn('secret', data)
        self.assertTrue(data['is_host'])

        # question_collections should include both the public and the user owned one
        self.assertIn('question_collections', data)
        returned = { qc['id'] for qc in data['question_collections'] }

        expected = set(
            QuestionCollection.objects
            .filter(Q(created_by__isnull=True) | Q(created_by=self.user), is_deleted=False)
            .values_list('id', flat=True)
        )
        self.assertSetEqual(returned, expected)

        # verify session and participant in db
        session = GameSession.objects.get(code=data['code'])
        self.assertEqual(session.status, 'pending')

        participant = session.participants.get(id=data['participant_id'])
        self.assertTrue(participant.is_host)
        self.assertEqual(participant.user, self.user)
