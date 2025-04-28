from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import QuestionCollection, Question
from .serializers import QuestionCollectionSerializer, QuestionSerializer
from django.db.models import Q

class QuestionCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionCollectionSerializer

    def get_permissions(self):
        # allow anonymous on list, but require auth everywhere else
        if self.action == 'list':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # list: public + (if logged in) your own
        if self.action == 'list':
            user = self.request.user
            if user.is_authenticated:
                return QuestionCollection.objects.filter(
                    Q(created_by=user) | Q(created_by__isnull=True)
                )
            # anonymous only public
            return QuestionCollection.objects.filter(created_by__isnull=True)

        # retrieve/update/destroy: only your own
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
