# backend/game/tests/test_available_characters.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from game.models import Character

class AvailableCharactersTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('available_characters')

        self.user1 = User.objects.create_user(username='user1', password='pw')
        self.user2 = User.objects.create_user(username='user2', password='pw')

        # Public character without image
        self.pub1 = Character.objects.create(
            name='PubNoImg',
            description='public no image',
            is_public=True,
            creator=None
        )
        # Public character with an image
        img = SimpleUploadedFile(
            'test.png',
            b'\x89PNG\r\n\x1a\n' + b'\x00'*100,
            content_type='image/png'
        )
        self.pub2 = Character.objects.create(
            name='PubWithImg',
            description='public with image',
            is_public=True,
            creator=None,
            image=img
        )
        # Private characters
        self.priv1 = Character.objects.create(
            name='PrivUser1',
            description='private to user1',
            is_public=False,
            creator=self.user1
        )
        self.priv2 = Character.objects.create(
            name='PrivUser2',
            description='private to user2',
            is_public=False,
            creator=self.user2
        )

    def test_anonymous_sees_only_public(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        returned_ids = {c['id'] for c in data}
        # Only pub1 and pub2
        self.assertSetEqual(returned_ids, {self.pub1.id, self.pub2.id})

    def test_anonymous_image_fields(self):
        resp = self.client.get(self.url)
        data = resp.json()
        # pub1 has no image
        no_img = next(c for c in data if c['id'] == self.pub1.id)
        self.assertIsNone(no_img['image'])
        # pub2 has an image URL ending with its file name
        with_img = next(c for c in data if c['id'] == self.pub2.id)
        self.assertIsNotNone(with_img['image'])
        self.assertTrue(with_img['image'].endswith(self.pub2.image.name))

    def test_user1_sees_public_and_own_private(self):
        self.client.force_authenticate(self.user1)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        returned_ids = {c['id'] for c in data}
        # Should include pub1, pub2, priv1 but not priv2
        self.assertSetEqual(returned_ids, {self.pub1.id, self.pub2.id, self.priv1.id})

    def test_user2_sees_public_and_own_private(self):
        self.client.force_authenticate(self.user2)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        returned_ids = {c['id'] for c in data}
        # Should include pub1, pub2, priv2 but not priv1
        self.assertSetEqual(returned_ids, {self.pub1.id, self.pub2.id, self.priv2.id})
