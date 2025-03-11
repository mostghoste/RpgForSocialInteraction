# game/api_views.py

import random, string
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import GameSession, Participant
from django.contrib.auth.models import AnonymousUser

def generate_room_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

@api_view(['POST'])
@permission_classes([AllowAny])
def create_room(request):
    user = request.user if request.user.is_authenticated else None
    
    attempts = 0
    while True:
        code = generate_room_code()
        if not GameSession.objects.filter(code=code).exists():
            break
        attempts += 1
        if attempts >= 100:
            return Response({'error': 'Serverio klaida: Nepavyko sukurti kambario.'}, status=500)

    # Create a new game session with default settings.
    session = GameSession.objects.create(code=code, host=user)
    # Add the creator as a participant.
    Participant.objects.create(user=user, game_session=session)
    # Return room details.
    return Response({
        'code': session.code,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
        'players': [user.username] if user else ["Guest"],
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def join_room(request):
    code = request.data.get('code', '').strip()
    if not code:
        return Response({'error': 'Prašome įrašyti kambario kodą!'}, status=400)
    try:
        session = GameSession.objects.get(code=code)
    except GameSession.DoesNotExist:
        return Response({'error': 'Kambarys su tokiu kodu neegzistuoja.'}, status=404)
    
    user = request.user if request.user.is_authenticated else None
    # Create a participant record. For guests, you might store a temporary name.
    Participant.objects.create(user=user, game_session=session)
    # Return the updated lobby state.
    players = list(session.participants.values_list('user__username', flat=True))
    # Replace any None (for guests) with "Guest"
    players = [p if p is not None else "Guest" for p in players]
    return Response({
        'code': session.code,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
        'players': players,
    })
