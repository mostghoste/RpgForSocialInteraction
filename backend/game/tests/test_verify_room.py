# backend/game/tests/test_verify_room.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse

from game.models import GameSession

class VerifyRoomTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # sample session
        self.session = GameSession.objects.create(
            code='ROOM123',
            round_length=75,
            round_count=5
        )
        self.url = reverse('verify_room')

    def test_missing_code_parameter(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Prašome įrašyti kambario kodą!'
        )

    def test_nonexistent_code(self):
        resp = self.client.get(self.url, {'code': 'BADCODE'})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json()['error'],
            'Kambarys su tokiu kodu neegzistuoja.'
        )

    def test_successful_verify(self):
        resp = self.client.get(self.url, {'code': self.session.code})
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        # check required fields
        self.assertEqual(data['code'], self.session.code)
        self.assertEqual(data['status'], self.session.status)
        self.assertEqual(data['round_length'], self.session.round_length)
        self.assertEqual(data['round_count'], self.session.round_count)
