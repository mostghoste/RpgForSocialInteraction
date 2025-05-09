# backend/game/tests/test_available_collections.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.urls import reverse
from game.models import QuestionCollection

class AvailableCollectionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('available_collections')

        self.user1 = User.objects.create_user(username='user1', password='pw')
        self.user2 = User.objects.create_user(username='user2', password='pw')

        self.public_coll = QuestionCollection.objects.create(name='Public', created_by=None)
        self.user1_coll = QuestionCollection.objects.create(name='User1Private', created_by=self.user1)
        self.user2_coll = QuestionCollection.objects.create(name='User2Private', created_by=self.user2)

    def test_anonymous_sees_only_public(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Only the public collection should be returned
        returned_ids = {c['id'] for c in data}
        self.assertSetEqual(returned_ids, {self.public_coll.id})
        self.assertEqual(data[0]['name'], self.public_coll.name)

    def test_user1_sees_public_and_own(self):
        self.client.force_authenticate(self.user1)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        returned_ids = {c['id'] for c in data}
        # Should include public and user1's private, but not user2's
        self.assertSetEqual(returned_ids, {self.public_coll.id, self.user1_coll.id})
        names = {c['name'] for c in data}
        self.assertIn(self.public_coll.name, names)
        self.assertIn(self.user1_coll.name, names)

    def test_user2_sees_public_and_own(self):
        self.client.force_authenticate(self.user2)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        returned_ids = {c['id'] for c in data}
        # Should include public and user2's private, but not user1's
        self.assertSetEqual(returned_ids, {self.public_coll.id, self.user2_coll.id})

    def test_deleted_collection_not_returned(self):
        self.public_coll.delete()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # No collections remain
        self.assertEqual(data, [])
