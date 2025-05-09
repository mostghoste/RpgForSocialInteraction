# game/tests/test_scoring.py

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

from game.models import (
    GameSession,
    Participant,
    Round,
    Message,
    Guess,
    Character,
    Question,
)
from game.scoring import compute_score_breakdown


class ComputeScoreBreakdownTests(TestCase):
    def setUp(self):
        self.session = GameSession.objects.create(code='SCORE1')

        self.host_user = User.objects.create_user(username='Host')
        self.host = Participant.objects.create(
            user=self.host_user,
            game_session=self.session,
            is_host=True,
            is_active=True,
        )

        self.user1 = User.objects.create_user(username='Player1')
        self.p1 = Participant.objects.create(
            user=self.user1,
            game_session=self.session,
            is_active=True,
        )

        self.user2 = User.objects.create_user(username='Player2')
        self.p2 = Participant.objects.create(
            user=self.user2,
            game_session=self.session,
            is_active=True,
        )

        # NPC
        self.char_npc = Character.objects.create(
            name='NPC Hero',
            description='robot',
            is_public=True,
            creator=None,
        )
        self.npc = Participant.objects.create(
            guest_identifier='npc1',
            guest_name='Bot',
            game_session=self.session,
            assigned_character=self.char_npc,
            is_npc=True,
            is_active=True,
        )

        self.char1 = Character.objects.create(
            name='Hero1', description='desc1', is_public=True, creator=None
        )
        self.char2 = Character.objects.create(
            name='Hero2', description='desc2', is_public=True, creator=None
        )
        self.p1.assigned_character = self.char1
        self.p1.save()
        self.p2.assigned_character = self.char2
        self.p2.save()

    def test_message_rewards(self):
        # Two rounds, one message in each
        q1 = Question.objects.create(text='Q1', creator=None)
        r1 = Round.objects.create(
            game_session=self.session,
            question=q1,
            round_number=1,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(seconds=60),
        )
        Message.objects.create(participant=self.p1, round=r1, text='hi')

        q2 = Question.objects.create(text='Q2', creator=None)
        r2 = Round.objects.create(
            game_session=self.session,
            question=q2,
            round_number=2,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(seconds=60),
        )
        Message.objects.create(participant=self.p1, round=r2, text='hello')

        breakdown, total = compute_score_breakdown(self.p1)

        descriptions = [item['description'] for item in breakdown]
        self.assertCountEqual(
            descriptions,
            [
                'už atsakymą 1 raunde',
                'už atsakymą 2 raunde',
                'už tai, kad niekas neatspėjo tavo personažo',
            ]
        )
        self.assertEqual(total, 100)

    def test_being_guessed_some(self):
        # p1 is guessed by p2 correctly, by host incorrectly
        Guess.objects.create(
            guesser=self.p2,
            guessed_participant=self.p1,
            guessed_character=self.char1,
            is_correct=True
        )
        Guess.objects.create(
            guesser=self.host,
            guessed_participant=self.p1,
            guessed_character=self.char2,
            is_correct=False
        )

        breakdown, total = compute_score_breakdown(self.p1)

        # Only one correct guess should appear
        expected = {
            'description': f'už tai, kad {self.user2.username} atspėjo tavo personažą',
            'points': 50
        }
        self.assertIn(expected, breakdown)
        self.assertEqual(total, 50)

    def test_being_guessed_none(self):
        # No one guesses p2
        breakdown, total = compute_score_breakdown(self.p2)

        expected = {
            'description': 'už tai, kad niekas neatspėjo tavo personažo',
            'points': 0
        }
        self.assertIn(expected, breakdown)
        self.assertEqual(total, 0)

    def test_being_guessed_all(self):
        # Both human players guess p1 correctly
        Guess.objects.create(
            guesser=self.p2,
            guessed_participant=self.p1,
            guessed_character=self.char1,
            is_correct=True
        )
        Guess.objects.create(
            guesser=self.host,
            guessed_participant=self.p1,
            guessed_character=self.char1,
            is_correct=True
        )

        breakdown, total = compute_score_breakdown(self.p1)

        expected = {
            'description': 'už tai, kad visi atspėjo tavo personažą',
            'points': 0
        }
        self.assertIn(expected, breakdown)
        self.assertEqual(total, 0)

    def test_correct_human_guess_rewards(self):
        # p1 guesses p2’s character correctly
        Guess.objects.create(
            guesser=self.p1,
            guessed_participant=self.p2,
            guessed_character=self.char2,
            is_correct=True
        )

        breakdown, total = compute_score_breakdown(self.p1)

        human_entry = {
            'description': f'už teisingai atpažintą žaidėją {self.user2.username}',
            'points': 100
        }
        self.assertIn(human_entry, breakdown)

        zero_entry = {
            'description': 'už tai, kad niekas neatspėjo tavo personažo',
            'points': 0
        }
        self.assertIn(zero_entry, breakdown)

        self.assertEqual(total, 100)

    def test_correct_npc_guess_rewards(self):
        # p1 guesses the NPC character correctly
        Guess.objects.create(
            guesser=self.p1,
            guessed_participant=self.npc,
            guessed_character=self.char_npc,
            is_correct=True
        )

        breakdown, total = compute_score_breakdown(self.p1)

        npc_entry = {
            'description': f'už teisingai atpažintą robotą „{self.char_npc.name}“',
            'points': 50
        }
        self.assertIn(npc_entry, breakdown)

        zero_entry = {
            'description': 'už tai, kad niekas neatspėjo tavo personažo',
            'points': 0
        }
        self.assertIn(zero_entry, breakdown)

        self.assertEqual(total, 50)
