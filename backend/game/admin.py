from django.contrib import admin
from .models import Character, GameSession, Participant, QuestionCollection, Question, Round, Message, Guess

admin.site.register(Character)
admin.site.register(GameSession)
admin.site.register(Participant)
admin.site.register(QuestionCollection)
admin.site.register(Question)
admin.site.register(Round)
admin.site.register(Message)
admin.site.register(Guess)