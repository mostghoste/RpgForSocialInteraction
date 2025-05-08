from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import QuestionCollection, Question
from .serializers import QuestionCollectionSerializer, QuestionSerializer
from django.db.models import Q
from django.core.exceptions import ValidationError

class QuestionCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionCollectionSerializer

    def get_permissions(self):
        # allow anonymous on list, but require auth everywhere else
        if self.action == 'list':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # list public and your own if logged in
        if self.action == 'list':
            user = self.request.user
            if user.is_authenticated:
                return QuestionCollection.objects.filter(
                    Q(created_by=user) | Q(created_by__isnull=True)
                ).filter(is_deleted=False)
            # anonymous only public
            return QuestionCollection.objects.filter(created_by__isnull=True, is_deleted=False)

        # retrieve/update/destroy: only your own
        return QuestionCollection.objects.filter(created_by=self.request.user, is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        coll = self.get_object()
        try:
            coll.delete()
        except ValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        coll = self.get_object()
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_question(self, request, pk=None):
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
        return Question.objects.filter(creator=self.request.user, is_deleted=False)
    
    def destroy(self, request, *args, **kwargs):
        q = self.get_object()
        try:
            q.delete()
        except ValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        q = self.get_object()
        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
