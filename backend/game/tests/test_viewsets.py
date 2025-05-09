# game/tests/test_viewsets.py

from django.urls import reverse
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from game.models import QuestionCollection, Question, GameSession, Round

class QuestionCollectionViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username="u1", password="pw")
        self.user2 = User.objects.create_user(username="u2", password="pw")
        self.public = QuestionCollection.objects.create(name="pub", created_by=None)
        self.private1 = QuestionCollection.objects.create(name="priv1", created_by=self.user1)
        self.private2 = QuestionCollection.objects.create(name="priv2", created_by=self.user2)
        # URLs
        self.list_url = reverse("questioncollection-list")
        self.detail1 = reverse("questioncollection-detail", args=[self.private1.pk])
        self.add_q1 = reverse("questioncollection-add-question", args=[self.private1.pk])

    def test_list_anonymous_sees_only_public(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        names = [c["name"] for c in resp.json()]
        self.assertIn("pub", names)
        self.assertNotIn("priv1", names)

    def test_list_auth_sees_public_and_own(self):
        self.client.force_authenticate(self.user1)
        resp = self.client.get(self.list_url)
        names = [c["name"] for c in resp.json()]
        self.assertIn("pub", names)
        self.assertIn("priv1", names)
        self.assertNotIn("priv2", names)

    def test_create_requires_auth(self):
        data = {"name": "new"}
        resp = self.client.post(self.list_url, data)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_and_owner_set(self):
        self.client.force_authenticate(self.user1)
        resp = self.client.post(self.list_url, {"name": "from1"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        coll = QuestionCollection.objects.get(name="from1")
        self.assertEqual(coll.created_by, self.user1)

    def test_destroy_unused_collection(self):
        self.client.force_authenticate(self.user1)
        resp = self.client.delete(self.detail1)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(QuestionCollection.objects.filter(pk=self.private1.pk).exists())

    def test_destroy_collection_in_active_session_fails(self):
        session = GameSession.objects.create(code="X")
        session.question_collections.add(self.private1)
        session.status = "in_progress"
        session.save()
        self.client.force_authenticate(self.user1)
        resp = self.client.delete(self.detail1)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("naudojama vykstančiame žaidime", resp.json()["error"])

    def test_update_collection_name(self):
        self.client.force_authenticate(self.user1)
        resp = self.client.patch(self.detail1, {"name": "renamed"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.private1.refresh_from_db()
        self.assertEqual(self.private1.name, "renamed")

    def test_update_collection_in_active_session_fails(self):
        session = GameSession.objects.create(code="Y")
        session.question_collections.add(self.private1)
        session.status = "guessing"
        session.save()
        self.client.force_authenticate(self.user1)
        resp = self.client.patch(self.detail1, {"name": "nope"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("naudojama vykstančiame žaidime", resp.json()["error"])

    def test_add_question_empty_text(self):
        self.client.force_authenticate(self.user1)
        resp = self.client.post(self.add_q1, {"text": ""})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["detail"], "Klausimas negali būti tuščias.")

    def test_add_question_success(self):
        self.client.force_authenticate(self.user1)
        resp = self.client.post(self.add_q1, {"text": "What?"})
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["text"], "What?")
        qid = body["id"]
        self.assertTrue(self.private1.questions.filter(pk=qid).exists())

class QuestionViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="qv", password="pw")
        # two questions owned by user
        self.q1 = Question.objects.create(text="A", creator=self.user)
        self.q2 = Question.objects.create(text="B", creator=self.user)
        # another user's question
        other = User.objects.create_user(username="other", password="pw")
        Question.objects.create(text="C", creator=other)

        self.list_url = reverse("question-list")
        self.detail1 = reverse("question-detail", args=[self.q1.pk])

    def test_list_only_own(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.list_url)
        texts = [q["text"] for q in resp.json()]
        self.assertCountEqual(texts, ["A", "B"])

    def test_create_question(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(self.list_url, {"text": "New"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Question.objects.filter(text="New", creator=self.user).exists())

    def test_update_question(self):
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.detail1, {"text": "A2"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.q1.refresh_from_db()
        self.assertEqual(self.q1.text, "A2")

    def test_destroy_unused_question(self):
        self.client.force_authenticate(self.user)
        resp = self.client.delete(self.detail1)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Question.objects.filter(pk=self.q1.pk).exists())

    def test_destroy_question_in_active_round_fails(self):
        # Create a session and put it in progress
        session = GameSession.objects.create(code="Z")
        session.status = "in_progress"
        session.save()
        # Create a live round using q2
        Round.objects.create(
            game_session=session,
            question=self.q2,
            round_number=1,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(seconds=30),
        )

        self.client.force_authenticate(self.user)
        detail2 = reverse("question-detail", args=[self.q2.pk])
        resp = self.client.delete(detail2)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("naudojamas vykstančiame žaidime", resp.json()["error"])

    def test_update_question_in_active_collection_fails(self):
        # q1 in a collection used by an in-progress session
        coll = QuestionCollection.objects.create(name="test", created_by=self.user)
        coll.questions.add(self.q1)
        session = GameSession.objects.create(code="W")
        session.question_collections.add(coll)
        session.status = "in_progress"
        session.save()

        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.detail1, {"text": "oops"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vykstančiame žaidime", resp.json()["error"])
