from rest_framework import serializers
from .models import QuestionCollection, Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']

class QuestionCollectionSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionCollection
        fields = ['id', 'name', 'description', 'questions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
