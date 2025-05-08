# backend/game/tests/test_update_settings.py

from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from game.models import GameSession, Participant, QuestionCollection

class UpdateSettingsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.host = User.objects.create_user(username='host', password='pw')
        self.session = GameSession.objects.create(code='ABCDEF')
        self.host_part = Participant.objects.create(
            user=self.host,
            game_session=self.session,
            is_host=True
        )

        self.coll1 = QuestionCollection.objects.create(name='Coll1', created_by=None)
        self.coll2 = QuestionCollection.objects.create(name='Coll2', created_by=None)

        # Assign only coll1 initially
        self.session.question_collections.set([self.coll1])
        self.session.save()

    def _payload(self, **kwargs):
        base = {
            'code': self.session.code,
            'participant_id': self.host_part.id,
            'secret': self.host_part.secret,
            'round_length': 60,
            'round_count': 3,
        }
        base.update(kwargs)
        return base

    def test_missing_required_params(self):
        url = reverse('update_settings')
        resp = self.client.post(url, data={})
        assert resp.status_code == 400
        assert resp.json()['error'] == 'Kambario kodas, dalyvio ID ir slaptažodis privalomi.'

    def test_invalid_room_or_participant(self):
        url = reverse('update_settings')
        # bad code
        resp = self.client.post(url, data={'code':'WRONG','participant_id':1,'secret':'x'})
        assert resp.status_code == 404
        assert 'Neteisingas' in resp.json()['error']

    def test_cannot_update_if_not_pending(self):
        self.session.status = 'in_progress'
        self.session.save()
        url = reverse('update_settings')
        resp = self.client.post(url, data=self._payload())
        assert resp.status_code == 400
        assert 'kai žaidimas jau prasidėjo' in resp.json()['error']

    def test_wrong_secret(self):
        url = reverse('update_settings')
        data = self._payload(secret='wrongsecret')
        resp = self.client.post(url, data=data)
        assert resp.status_code == 403
        assert 'Netinkamas slaptažodis' in resp.json()['error']

    def test_only_host_can_update(self):
        # make a non-host participant
        other = User.objects.create_user(username='other', password='pw')
        p2 = Participant.objects.create(user=other, game_session=self.session, is_host=False)
        url = reverse('update_settings')
        resp = self.client.post(url, data={
            'code': self.session.code,
            'participant_id': p2.id,
            'secret': p2.secret,
            'round_length': 60,
            'round_count': 3
        })
        assert resp.status_code == 403
        assert 'Tik vedėjas gali keisti nustatymus' in resp.json()['error']

    def test_invalid_round_settings(self):
        url = reverse('update_settings')
        # negative and zero
        for rl, rc in [(-1, 3), (60, 0), (2000, 3), (60, 30)]:
            resp = self.client.post(url, data=self._payload(round_length=rl, round_count=rc))
            assert resp.status_code == 400
            assert 'Neteisingi raundų nustatymų duomenys' in resp.json()['error']

    def test_invalid_guess_timer(self):
        url = reverse('update_settings')
        # non-integer
        resp = self.client.post(url, data=self._payload(guess_timer='abc'))
        assert resp.status_code == 400
        assert 'Neteisingi spėjimų laiko nustatymo duomenys' in resp.json()['error']

        # too large
        resp = self.client.post(url, data=self._payload(guess_timer=1000))
        assert resp.status_code == 400
        assert 'Neteisingi spėjimų laiko nustatymo duomenys' in resp.json()['error']

    def test_success_without_guess_timer(self):
        url = reverse('update_settings')
        resp = self.client.post(url, data=self._payload(round_length=120, round_count=5), format='json')
        assert resp.status_code == 200

        data = resp.json()
        assert data['round_length'] == 120
        assert data['round_count'] == 5
        # guess_timer unchanged (default is 60)
        assert data['guess_timer'] == self.session.guess_timer

        # DB was updated
        self.session.refresh_from_db()
        assert self.session.round_length == 120
        assert self.session.round_count == 5

    def test_success_with_guess_timer_and_collections(self):
        url = reverse('update_settings')
        # pick coll2 instead of coll1
        resp = self.client.post(
            url,
            data=self._payload(
                round_length=90,
                round_count=4,
                guess_timer=30,
                selectedCollections=[self.coll2.id]
            ),
            format='json'
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data['round_length'] == 90
        assert data['round_count'] == 4
        assert data['guess_timer'] == 30

        # collections list returned matches coll2 only
        names = {c['name'] for c in data['question_collections']}
        assert names == {'Coll2'}

        # DB reflects change
        self.session.refresh_from_db()
        assert self.session.guess_timer == 30
        assert list(self.session.question_collections.all()) == [self.coll2]

    def test_cannot_add_unowned_collection(self):
        # Create a collection owned by someone else
        other = User.objects.create_user(username='attacker', password='pw')
        external = QuestionCollection.objects.create(
            name='BadColl',
            created_by=other
        )

        url = reverse('update_settings')
        payload = self._payload(
            round_length=80,
            round_count=2,
            selectedCollections=[self.coll1.id, external.id]
        )
        resp = self.client.post(url, data=payload, format='json')
        assert resp.status_code == 400
        err = resp.json().get('error', '').lower()
        assert 'kolekcij' in err

        # DB should remain unchanged
        self.session.refresh_from_db()
        assert list(self.session.question_collections.all()) == [self.coll1]

    def test_guest_host_cannot_add_user_owned_collection(self):
        # Create a fresh session with a guest host
        session2 = GameSession.objects.create(code='GUEST1')
        guest_host = Participant.objects.create(
            guest_identifier='guest1234',
            guest_name='GuestHost',
            game_session=session2,
            is_host=True
        )

        public = QuestionCollection.objects.create(name='PublicColl', created_by=None)
        private = QuestionCollection.objects.create(name='PrivateColl', created_by=self.host)

        url = reverse('update_settings')
        payload = {
            'code': session2.code,
            'participant_id': guest_host.id,
            'secret': guest_host.secret,
            'round_length': 45,
            'round_count': 3,
            'selectedCollections': [public.id, private.id],
        }

        resp = self.client.post(url, data=payload, format='json')
        assert resp.status_code == 400
        err = resp.json()['error'].lower()
        assert 'kolekcij' in err

        # session2 should still have no collections
        session2.refresh_from_db()
        assert list(session2.question_collections.all()) == []
