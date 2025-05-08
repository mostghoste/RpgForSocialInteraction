# backend/game/tests/test_leave_room.py

from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from game.models import GameSession, Participant

class LeaveRoomTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session = GameSession.objects.create(code='ZZZZZZ')
        self.user1 = User.objects.create_user(username='user1', password='pw')
        self.user2 = User.objects.create_user(username='user2', password='pw')

        # Host and a second participant
        self.host = Participant.objects.create(
            user=self.user1,
            game_session=self.session,
            is_host=True
        )
        self.other = Participant.objects.create(
            user=self.user2,
            game_session=self.session,
            is_host=False
        )

    def url(self):
        return reverse('leave_room')

    def payload(self, participant, secret):
        return {
            'code': self.session.code,
            'participant_id': participant.id,
            'secret': secret
        }

    def test_missing_required_params(self):
        resp = self.client.post(self.url(), data={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()['error'],
            'Kambario kodas, dalyvio ID ir slaptažodis privalomi.'
        )

    def test_invalid_room_or_participant(self):
        resp = self.client.post(self.url(), data={
            'code': 'BADCODE',
            'participant_id': 9999,
            'secret': 'nope'
        })
        self.assertEqual(resp.status_code, 404)
        self.assertIn('Neteisingas', resp.json()['error'])

    def test_wrong_secret(self):
        resp = self.client.post(
            self.url(),
            data=self.payload(self.host, 'wrongsecret')
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn('Netinkamas slaptažodis', resp.json()['error'])

    def test_leave_pending_last_participant_deletes_session(self):
        self.other.delete()

        resp = self.client.post(
            self.url(),
            data=self.payload(self.host, self.host.secret)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['message'], 'Išėjote iš kambario.')
        # Session should be deleted
        with self.assertRaises(GameSession.DoesNotExist):
            GameSession.objects.get(code=self.session.code)

    def test_leave_pending_host_transfers_host(self):
        # Host leaves while another human remains
        resp = self.client.post(
            self.url(),
            data=self.payload(self.host, self.host.secret)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['message'], 'Išėjote iš kambario.')

        # Session still exists
        session = GameSession.objects.get(code=self.session.code)
        # Remaining user should now be host
        new_host = session.participants.get(id=self.other.id)
        self.assertTrue(new_host.is_host)
        # Old host should be gone
        self.assertFalse(
            session.participants.filter(id=self.host.id).exists()
        )

    def test_leave_in_progress_deactivates_and_transfers(self):
        # Move session to in_progress
        self.session.status = 'in_progress'
        self.session.save()

        # Host leaves
        resp = self.client.post(
            self.url(),
            data=self.payload(self.host, self.host.secret)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['message'], 'Išėjote iš kambario.')

        # Participant marked inactive
        host = Participant.objects.get(pk=self.host.id)
        self.assertFalse(host.is_active)

        # The other user becomes host
        other = Participant.objects.get(pk=self.other.id)
        self.assertTrue(other.is_host)
        # Session still exists
        GameSession.objects.get(code=self.session.code)

    def test_leave_in_progress_last_human_keeps_session(self):
        # Only one human, session in_progress
        self.other.delete()
        self.session.status = 'in_progress'
        self.session.save()

        resp = self.client.post(
            self.url(),
            data=self.payload(self.host, self.host.secret)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['message'], 'Išėjote iš kambario.')

        # Host is now inactive
        host = Participant.objects.get(pk=self.host.id)
        self.assertFalse(host.is_active)
        # Session remains (no auto-deletion in in_progress)
        GameSession.objects.get(code=self.session.code)
