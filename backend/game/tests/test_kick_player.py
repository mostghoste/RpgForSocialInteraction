from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from game.models import GameSession, Participant
import game.api_views as views

views.broadcast_lobby_update = lambda *args, **kwargs: None

class KickPlayerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('kick_player')

        self.session = GameSession.objects.create(code='KICK1')
        self.user = User.objects.create_user(username='host', password='pw')
        self.host = Participant.objects.create(
            user=self.user,
            game_session=self.session,
            is_host=True
        )

        self.target = Participant.objects.create(
            guest_identifier='t1',
            guest_name='Target',
            game_session=self.session,
            is_host=False
        )

    def test_missing_params(self):
        resp = self.client.post(self.url, data={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Trūksta privalomų parametrų.')

    def test_invalid_session_or_host_id(self):
        # wrong code
        resp = self.client.post(self.url, data={
            'code': 'WRONG',
            'participant_id': self.host.id,
            'secret': self.host.secret,
            'target_participant_id': self.target.id
        })
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], 'Neteisingas kambarys arba dalyvio ID.')

        # wrong host id
        resp2 = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': 9999,
            'secret': self.host.secret,
            'target_participant_id': self.target.id
        })
        self.assertEqual(resp2.status_code, 404)
        self.assertEqual(resp2.json()['error'], 'Neteisingas kambarys arba dalyvio ID.')

    def test_wrong_secret(self):
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': 'badsecret',
            'target_participant_id': self.target.id
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Netinkamas slaptažodis.')

    def test_non_host_cannot_kick(self):
        self.host.is_host = False
        self.host.save()
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret,
            'target_participant_id': self.target.id
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Tik vedėjas gali išmesti žaidėjus.')

    def test_target_not_found(self):
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret,
            'target_participant_id': 9999
        })
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()['error'], 'Dalyvis nerastas.')

    def test_cannot_kick_self(self):
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret,
            'target_participant_id': self.host.id
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()['error'], 'Negalite išmesti savęs.')

    def test_kick_deletes_in_pending(self):
        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret,
            'target_participant_id': self.target.id
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'Dalyvis pašalintas.'})
        # target should be removed
        self.assertFalse(Participant.objects.filter(id=self.target.id).exists())

    def test_kick_deactivates_in_progress(self):
        # switch to in_progress
        self.session.status = 'in_progress'
        self.session.save()

        resp = self.client.post(self.url, data={
            'code': self.session.code,
            'participant_id': self.host.id,
            'secret': self.host.secret,
            'target_participant_id': self.target.id
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'message': 'Dalyvis pašalintas.'})
        # participant still exists but is_active=False
        tgt = Participant.objects.get(id=self.target.id)
        self.assertFalse(tgt.is_active)
