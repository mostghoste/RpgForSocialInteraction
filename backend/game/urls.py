# game/urls.py

from django.urls import path, include
from rest_framework import routers
from .api_viewsets import QuestionCollectionViewSet, QuestionViewSet
from .api_views import (
    create_room,
    join_room,
    update_settings,
    update_question_collections,
    available_collections,
    verify_room,
    lobby_state,
    leave_room,
    start_game,
    select_character,
    create_character,
    available_characters,
    send_chat_message,
    submit_guesses,
    available_guess_options,
    add_npc,
    kick_player
)

router = routers.DefaultRouter()
router.register(r'question_collections', QuestionCollectionViewSet, basename='questioncollection')
router.register(r'questions', QuestionViewSet, basename='question')

urlpatterns = router.urls + [
    path('create_room/', create_room, name='create_room'),
    path('join_room/', join_room, name='join_room'),
    path('update_settings/', update_settings, name='update_settings'),
    path('update_question_collections/', update_question_collections, name='update_question_collections'),
    path('available_collections/', available_collections, name="available_collections"),
    path('verify_room/', verify_room, name='verify_room'),
    path('lobby_state/', lobby_state, name='lobby_state'),
    path('leave_room/', leave_room, name='leave_room'),
    path('start_game/', start_game, name='start_game'),
    path('select_character/', select_character, name='select_character'),
    path('create_character/', create_character, name='create_character'),
    path('available_characters/', available_characters, name='available_characters'),
    path('send_chat_message/', send_chat_message, name='send_chat_message'),
    path('submit_guesses/', submit_guesses, name='submit_guesses'),
    path('available_guess_options/', available_guess_options, name='available_guess_options'),
    path('add_npc/', add_npc, name='add_npc'),
    path('kick_player/', kick_player, name='kick_player'),
]
