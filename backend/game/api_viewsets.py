from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import QuestionCollection, Question
from .serializers import QuestionCollectionSerializer, QuestionSerializer
from django.db.models import Q

class QuestionCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.action == 'list':
            # show global + mine
            return QuestionCollection.objects.filter(
                Q(created_by=self.request.user) | Q(created_by__isnull=True)
            )
        # for retrieve/update/destroy only my own
        return QuestionCollection.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def add_question(self, request, pk=None):
        """
        POST /api/question_collections/{pk}/add_question/
        { "text": "What is your quest?" }
        """
        collection = self.get_object()
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'detail': 'Klausimas negali būti tuščias.'}, status=400)
        q = Question.objects.create(text=text, creator=request.user)
        collection.questions.add(q)
        return Response(QuestionSerializer(q).data, status=201)


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Question.objects.filter(creator=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
