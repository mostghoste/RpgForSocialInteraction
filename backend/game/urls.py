# game/urls.py
from django.urls import path
from .api_views import create_room, join_room, update_settings, update_question_collections, available_collections, verify_room, lobby_state

urlpatterns = [
    path('create_room/', create_room, name='create_room'),
    path('join_room/', join_room, name='join_room'),
    path('update_settings/', update_settings, name='update_settings'),
    path('update_question_collections/', update_question_collections, name='update_question_collections'),
    path('available_collections/', available_collections, name="available_collections"),
    path('verify_room/', verify_room, name='verify_room'),
    path('lobby_state/', lobby_state, name='lobby_state'),
]