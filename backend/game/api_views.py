# game/api_views.py

import random, string, uuid
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
    if session.status != 'pending':
        return Response({'error': 'Žaidimas jau prasidėjo arba baigėsi.'}, status=400)

    user = request.user if request.user.is_authenticated else None
    guest_username = request.data.get('guest_username', '').strip() or None

    if not user:
        # Always create a new Participant for unauthenticated users.
        participant = Participant.objects.create(
            user=None,
            game_session=session,
            guest_identifier=str(uuid.uuid4()),
            guest_name=guest_username
        )
    else:
        participant, created = Participant.objects.get_or_create(
            user=user,
            game_session=session,
            defaults={'guest_name': guest_username}
        )
        # Optionally update guest_name if provided
        if guest_username and not created:
            participant.guest_name = guest_username
            participant.save()

    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)

    players = []
    for part in session.participants.all():
        if part.user:
            players.append(part.user.username)
        else:
            players.append(
                part.guest_name if part.guest_name else (f"Guest {part.guest_identifier[:8]}" if part.guest_identifier else "Guest")
            )

    return Response({
        'code': session.code,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
        'players': players,
        'participant_id': participant.id
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def leave_room(request):
    code = request.data.get('code', '').strip()
    if not code:
        return Response({'error': 'Kambario kodas privalomas.'}, status=400)
    try:
        session = GameSession.objects.get(code=code)
    except GameSession.DoesNotExist:
        return Response({'error': 'Toks kambarys nebuvo rastas.'}, status=404)
    
    user = request.user if request.user.is_authenticated else None
    # Remove the participant record (if it exists)
    Participant.objects.filter(user=user, game_session=session).delete()
    
    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)
    
    return Response({'message': 'Išėjote iš kambario.'})

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_room(request):
    code = request.query_params.get('code', '').strip()
    if not code:
        return Response({'error': 'Prašome įrašyti kambario kodą!'}, status=400)
    try:
        session = GameSession.objects.get(code=code)
    except GameSession.DoesNotExist:
        return Response({'error': 'Kambarys su tokiu kodu neegzistuoja.'}, status=404)
    if session.status != 'pending':
        return Response({'error': 'Žaidimas jau prasidėjo arba baigėsi.'}, status=400)
    return Response({
        'code': session.code,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def lobby_state(request):
    code = request.query_params.get('code', '').strip()
    if not code:
        return Response({'error': 'Kambario kodas privalomas.'}, status=400)
    try:
        session = GameSession.objects.get(code=code)
    except GameSession.DoesNotExist:
        return Response({'error': 'Toks kambarys nebuvo rastas.'}, status=404)
    
    players = []
    for part in session.participants.all():
        if part.user:
            players.append(part.user.username)
        else:
            # Use guest_name if set, otherwise a default based on guest_identifier.
            players.append(part.guest_name if part.guest_name else (f"Guest {part.guest_identifier[:8]}" if part.guest_identifier else "Guest"))
    
    data = {
        'code': session.code,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
        'players': players,
    }
    return Response(data)
