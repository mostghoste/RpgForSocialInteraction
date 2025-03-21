# game/api_views.py

import random, string, uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import GameSession, Participant, QuestionCollection
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
        'secret': participant.secret,
        'is_host': participant.is_host,
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def update_settings(request):
    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    provided_secret = request.data.get('secret', '').strip()
    round_length = request.data.get('round_length')
    round_count = request.data.get('round_count')

    if not code or not participant_id or not provided_secret:
         return Response({'error': 'Kambario kodas, dalyvio ID ir slaptažodis privalomi.'}, status=400)
    try:
         session = GameSession.objects.get(code=code)
         participant = session.participants.get(id=participant_id)
    except (GameSession.DoesNotExist, Participant.DoesNotExist):
         return Response({'error': 'Neteisingas kambarys arba dalyvio ID.'}, status=404)
    
    if session.status != 'pending':
        return Response({'error': 'Negalima keisti kambario nustatymų, kai žaidimas jau prasidėjo.'}, status=400)


    if participant.secret != provided_secret:
         return Response({'error': 'Netinkamas slaptažodis.'}, status=403)

    if not participant.is_host:
         return Response({'error': 'Tik vedėjas gali keisti nustatymus.'}, status=403)

    try:
         round_length = int(round_length)
         round_count = int(round_count)
         if round_length <= 0 or round_length > 1200 or round_count <= 0 or round_count > 20:
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
def leave_room(request):
    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    provided_secret = request.data.get('secret', '').strip()
    if not code or not participant_id or not provided_secret:
         return Response({'error': 'Kambario kodas, dalyvio ID ir slaptažodis privalomi.'}, status=400)
    try:
         session = GameSession.objects.get(code=code)
         participant = session.participants.get(id=participant_id)
    except (GameSession.DoesNotExist, Participant.DoesNotExist):
         return Response({'error': 'Neteisingas kambarys arba dalyvio ID.'}, status=404)

    if participant.secret != provided_secret:
         return Response({'error': 'Netinkamas slaptažodis.'}, status=403)

    was_host = participant.is_host
    participant.delete()

    remaining = session.participants.all()
    if remaining.exists():
         # If the leaving participant was the host, transfer host privileges
         if was_host:
             oldest = remaining.order_by('joined_at').first()
             oldest.is_host = True
             oldest.save()
         from .utils import broadcast_lobby_update
         broadcast_lobby_update(session)
         return Response({'message': 'Išėjote iš kambario.'})
    else:
         # If no participants remain, delete the session.
         session.delete()
         return Response({'message': 'Jūs buvote paskutinis kambaryje. Kambarys ištrintas.'})


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

@api_view(['POST'])
@permission_classes([AllowAny])
def update_question_collections(request):
    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    provided_secret = request.data.get('secret', '').strip()
    collections_ids = request.data.get('collections', [])

    if not code or not participant_id or not provided_secret:
        return Response({'error': 'Kambario kodas, dalyvio ID ir slaptažodis privalomi.'}, status=400)

    try:
        session = GameSession.objects.get(code=code)
        participant = session.participants.get(id=participant_id)
    except (GameSession.DoesNotExist, Participant.DoesNotExist):
        return Response({'error': 'Neteisingas kambarys arba dalyvio ID.'}, status=404)
    
    if session.status != 'pending':
         return Response({'error': 'Negalima keisti klausimų kolekcijų, kai žaidimas jau prasidėjo.'}, status=400)

    if participant.secret != provided_secret:
        return Response({'error': 'Netinkamas slaptažodis.'}, status=403)

    if not participant.is_host:
        return Response({'error': 'Tik vedėjas gali keisti klausimų kolekcijas.'}, status=403)

    # Fetch valid collections from the provided IDs
    valid_collections = QuestionCollection.objects.filter(id__in=collections_ids)
    # Update the session's question collections.
    session.question_collections.set(valid_collections)
    session.save()

    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)

    collections_list = list(session.question_collections.values('id', 'name'))
    return Response({
         'code': session.code,
         'question_collections': collections_list,
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def available_collections(request):
    collections = QuestionCollection.objects.all().values('id', 'name')
    return Response(list(collections))

@api_view(['POST'])
@permission_classes([AllowAny])
def select_character(request):
    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    provided_secret = request.data.get('secret', '').strip()
    character_id = request.data.get('character_id')
    
    if not code or not participant_id or not provided_secret or not character_id:
        return Response({'error': 'Trūksta privalomų parametrų.'}, status=400)
    
    try:
        session = GameSession.objects.get(code=code)
        participant = session.participants.get(id=participant_id)
    except (GameSession.DoesNotExist, Participant.DoesNotExist):
        return Response({'error': 'Neteisingas kambario kodas arba dalyvio ID.'}, status=404)
    
    if session.status != 'pending':
         return Response({'error': 'Negalima keisti personažų, kai žaidimas jau prasidėjo.'}, status=400)
    
    if participant.secret != provided_secret:
        return Response({'error': 'Neteisingas slaptažodis.'}, status=403)
    
    try:
        from .models import Character
        character = Character.objects.get(id=character_id)
    except Character.DoesNotExist:
        return Response({'error': 'Personažas nerastas.'}, status=404)

    if session.participants.filter(assigned_character=character).exists():
        return Response({'error': 'Šis personažas jau pasirinktas.'}, status=400)
    
    participant.assigned_character = character
    participant.save()
    
    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)
    
    return Response({'message': 'Personažas pasirinktas.'})

@api_view(['POST'])
@permission_classes([AllowAny])
def create_character(request):
    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    provided_secret = request.data.get('secret', '').strip()
    name = request.data.get('name', '').strip()
    description = request.data.get('description', '').strip()
    
    if not code or not participant_id or not provided_secret or not name:
        return Response({'error': 'Trūksta privalomų parametrų.'}, status=400)
    
    try:
        session = GameSession.objects.get(code=code)
        participant = session.participants.get(id=participant_id)
    except (GameSession.DoesNotExist, Participant.DoesNotExist):
        return Response({'error': 'Neteisingas kambario kodas arba dalyvio ID.'}, status=404)
    
    if session.status != 'pending':
        return Response({'error': 'Negalima keisti personažų, kai žaidimas jau prasidėjo.'}, status=400)
    
    
    if participant.secret != provided_secret:
        return Response({'error': 'Neteisingas slaptažodis.'}, status=403)
    
    from .models import Character
    user = request.user if request.user.is_authenticated else None
    new_character = Character.objects.create(name=name, description=description, creator=user)
    
    participant.assigned_character = new_character
    participant.save()
    
    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)
    
    return Response({'message': 'Personažas sukurtas ir pasirinktas.', 'character_id': new_character.id})

@api_view(['GET'])
@permission_classes([AllowAny])
def available_characters(request):
    from .models import Character
    characters = Character.objects.filter(creator__username="mostghoste").values('id', 'name', 'description')
    return Response(list(characters))


@api_view(['POST'])
@permission_classes([AllowAny])
def start_game(request):
    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    provided_secret = request.data.get('secret', '').strip()

    if not code or not participant_id or not provided_secret:
         return Response({'error': 'Kambario kodas, dalyvio ID ir slaptažodis privalomi.'}, status=400)
    
    try:
         session = GameSession.objects.get(code=code)
         participant = session.participants.get(id=participant_id)
    except (GameSession.DoesNotExist, Participant.DoesNotExist):
         return Response({'error': 'Neteisingas kambarys arba dalyvio ID.'}, status=404)

    if participant.secret != provided_secret:
         return Response({'error': 'Netinkamas slaptažodis.'}, status=403)

    if not participant.is_host:
         return Response({'error': 'Tik vedėjas gali pradėti žaidimą.'}, status=403)
    
    if session.status != 'pending':
         return Response({'error': 'Žaidimas jau prasidėjo arba baigėsi.'}, status=400)

    if session.participants.count() < 3:
         return Response({'error': 'Žaidimui reikia bent 3 dalyvių.'}, status=400)
    
    if session.participants.filter(assigned_character__isnull=True).exists():
         return Response({'error': 'Kiekvienas dalyvis privalo turėti personažą.'}, status=400)
    
    total_questions = sum(collection.questions.count() for collection in session.question_collections.all())
    if total_questions <= session.round_count:
         return Response({'error': 'Klausimų kolekcijose nepakanka klausimų pagal nurodytą raundų skaičių.'}, status=400)

    # All checks passed; change game status.
    session.status = 'in_progress'
    session.save()

    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)

    return Response({
         'message': 'Žaidimas pradėtas.',
         'code': session.code,
         'status': session.status,
         'round_length': session.round_length,
         'round_count': session.round_count,
    })
