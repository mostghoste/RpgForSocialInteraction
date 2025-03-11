# game/urls.py

from django.urls import path
from .api_views import create_room, join_room

urlpatterns = [
    path('create_room/', create_room, name='create_room'),
    path('join_room/', join_room, name='join_room'),
]
