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
    attempts = 0
    while True:
        code = generate_room_code()
        if not GameSession.objects.filter(code=code).exists():
            break
        attempts += 1
        if attempts >= 100:
            return Response({'error': 'Serverio klaida: Nepavyko sukurti kambario.'}, status=500)

    session = GameSession.objects.create(code=code)
    
    return Response({
        'code': session.code,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def update_settings(request):
    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    round_length = request.data.get('round_length')
    round_count = request.data.get('round_count')

    if not code or not participant_id:
         return Response({'error': 'Kambario kodas ir dalyvio ID privalomi.'}, status=400)
    try:
         session = GameSession.objects.get(code=code)
         participant = session.participants.get(id=participant_id)
    except (GameSession.DoesNotExist, Participant.DoesNotExist):
         return Response({'error': 'Neteisingas kambarys arba dalyvio ID.'}, status=404)

    if not participant.is_host:
         return Response({'error': 'Tik vedėjas gali keisti nustatymus.'}, status=403)

    try:
         round_length = int(round_length)
         round_count = int(round_count)
         if round_length <= 0 or round_count <= 0:
              raise ValueError
    except (ValueError, TypeError):
         return Response({'error': 'Neteisingi nustatymų duomenys.'}, status=400)

    session.round_length = round_length
    session.round_count = round_count
    session.save()

    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)

    return Response({
         'code': session.code,
         'status': session.status,
         'round_length': session.round_length,
         'round_count': session.round_count,
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

    # For guests, get the username from the request.
    guest_username = None
    if not user:
        guest_username = request.data.get('guest_username', '').strip()

    # Use the appropriate name.
    name_to_join = user.username if user else guest_username
    if not name_to_join:
        return Response({'error': 'Prašome įvesti vartotojo vardą.'}, status=400)

    # Check for duplicate names in the room (case-insensitive).
    existing_names = []
    for part in session.participants.all():
        if part.user:
            existing_names.append(part.user.username.lower())
        elif part.guest_name:
            existing_names.append(part.guest_name.lower())
    if name_to_join.lower() in existing_names:
        return Response({'error': 'Toks vartotojo vardas jau naudojamas kambaryje.'}, status=400)

    # Determine if this is the first participant in the room.
    is_host_flag = (session.participants.count() == 0)

    # Create (or update) the participant record.
    if user:
        participant, created = Participant.objects.get_or_create(
            user=user,
            game_session=session,
            defaults={'is_host': is_host_flag}
        )
        display_name = user.username
    else:
        # For guests, also check if a participant_id is provided (e.g. from localStorage)
        participant_id = request.data.get('participant_id')
        if participant_id:
            try:
                participant = session.participants.get(id=participant_id, user__isnull=True)
            except Participant.DoesNotExist:
                participant = None
        else:
            participant = None

        if participant:
            # Update the guest name if necessary.
            if participant.guest_name != guest_username:
                participant.guest_name = guest_username
                participant.save()
        else:
            participant = Participant.objects.create(
                user=None,
                game_session=session,
                guest_identifier=str(uuid.uuid4()),
                guest_name=guest_username,
                is_host=is_host_flag
            )
        display_name = guest_username

    # Broadcast the updated lobby state.
    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)

    # Collect player names.
    players = []
    for part in session.participants.all():
        if part.user:
            players.append(part.user.username)
        else:
            players.append(part.guest_name if part.guest_name else (f"Guest {part.guest_identifier[:8]}" if part.guest_identifier else "Guest"))

    return Response({
        'code': session.code,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
        'players': players,
        'participant_id': participant.id,
        'is_host': participant.is_host,
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
