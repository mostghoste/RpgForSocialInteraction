# game/tests/test_soft_delete.py
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from game.models import (
    Question,
    QuestionCollection,
    GameSession,
    Round,
)
from django.contrib.auth.models import User

class SoftDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dummy", password="x")
        self.session = GameSession.objects.create(code="S1", status="pending")
        self.question = Question.objects.create(text="What?", creator=self.user)
        self.collection = QuestionCollection.objects.create(name="C1", created_by=self.user)
        self.collection.questions.add(self.question)

    def test_question_delete_when_unused(self):
        # no rounds, no active session - delete should work
        self.assertTrue(Question.objects.filter(pk=self.question.pk).exists())
        self.question.delete()
        self.assertFalse(Question.objects.filter(pk=self.question.pk).exists())

    def test_question_delete_in_active_round(self):
        # put question into a live round
        self.session.status = "in_progress"
        self.session.save(update_fields=["status"])
        Round.objects.create(
            game_session=self.session,
            question=self.question,
            round_number=1,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(seconds=60),
        )
        with self.assertRaises(ValidationError) as cm:
            self.question.delete()
        self.assertIn("naudojamas vykstančiame žaidime", str(cm.exception))

    def test_question_delete_in_collection_of_active_session(self):
        # attach the collection to the session, mark session active
        self.session.question_collections.add(self.collection)
        self.session.status = "guessing"
        self.session.save(update_fields=["status"])
        # should block because the collection is in use
        with self.assertRaises(ValidationError) as cm:
            self.question.delete()
        self.assertIn("naudojamas vykstančiame žaidime", str(cm.exception))

    def test_collection_delete_when_unused(self):
        # session is pending by default, so deletion is allowed
        self.assertTrue(QuestionCollection.objects.filter(pk=self.collection.pk).exists())
        self.collection.delete()
        self.assertFalse(QuestionCollection.objects.filter(pk=self.collection.pk).exists())

    def test_collection_delete_in_active_session(self):
        # attach to session and make it in_progress
        self.session.question_collections.add(self.collection)
        self.session.status = "in_progress"
        self.session.save(update_fields=["status"])
        with self.assertRaises(ValidationError) as cm:
            self.collection.delete()
        self.assertIn("kolekcijos, kuri naudojama vykstančiame žaidime", str(cm.exception))

    def test_collection_save_if_in_active_session(self):
        # attach & activate session
        self.session.question_collections.add(self.collection)
        self.session.status = "guessing"
        self.session.save(update_fields=["status"])
        # try to rename
        self.collection.name = "New Name"
        with self.assertRaises(ValidationError) as cm:
            self.collection.save()
        self.assertIn("Negalite keisti klausimų kolekcijos", str(cm.exception))

    def test_collection_save_unattached_or_pending(self):
        # rename while session still pending
        self.collection.name = "New Name"
        # should not raise
        self.collection.save()
        # attach but leave pending
        self.session.question_collections.add(self.collection)
        self.collection.name = "Another Name"
        self.collection.save()
        self.assertEqual(QuestionCollection.objects.get(pk=self.collection.pk).name, "Another Name")
