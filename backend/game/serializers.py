from rest_framework import serializers
from .models import QuestionCollection, Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']

class QuestionCollectionSerializer(serializers.ModelSerializer):
    is_standard = serializers.SerializerMethodField()
    is_mine      = serializers.SerializerMethodField()
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model  = QuestionCollection
        fields = [
          'id',
          'name',
          'description',
          'questions',
          'created_at',
          'updated_at',
          'is_standard',
          'is_mine'
        ]
        read_only_fields = ['id','created_at','updated_at','is_standard','is_mine']

    def get_is_standard(self, obj):
        return obj.created_by is None

    def get_is_mine(self, obj):
        user = self.context['request'].user
        return bool(user and obj.created_by == user)

