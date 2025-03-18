# game/urls.py

from django.urls import path
from .api_views import create_room, join_room, verify_room, lobby_state, update_settings

urlpatterns = [
    path('create_room/', create_room, name='create_room'),
    path('join_room/', join_room, name='join_room'),
    path('verify_room/', verify_room, name='verify_room'),
    path('lobby_state/', lobby_state, name='lobby_state'),
    path('update_settings/', update_settings, name='update_settings'),
]
