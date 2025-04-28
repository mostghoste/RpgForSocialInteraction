from django.contrib import admin
from .models import (
    Character, GameSession, Participant,
    QuestionCollection, Question, Round, Message, Guess
)

admin.site.register(Character)
admin.site.register(GameSession)
admin.site.register(Participant)
admin.site.register(Round)
admin.site.register(Message)
admin.site.register(Guess)

@admin.register(QuestionCollection)
class QuestionCollectionAdmin(admin.ModelAdmin):
    list_filter = ('is_deleted',)
    actions = ['restore_collections']

    def get_queryset(self, request):
        # include soft‐deleted ones
        return QuestionCollection.all_objects.all()

    @admin.action(description="Restore selected collections")
    def restore_collections(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_filter = ('is_deleted',)
    actions = ['restore_questions']

    def get_queryset(self, request):
        # include soft‐deleted ones
        return Question.all_objects.all()

    @admin.action(description="Restore selected questions")
    def restore_questions(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)
