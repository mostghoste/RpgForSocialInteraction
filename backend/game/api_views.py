# game/api_views.py

import random, string, uuid
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import GameSession, Participant, QuestionCollection, Message, Round, Character
from django.utils import timezone
from django.db.models import F, Q
from .utils import broadcast_chat_message, broadcast_lobby_update, broadcast_round_update, send_system_message

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
    
    if request.user and request.user.is_authenticated:
        participant = Participant.objects.create(
            user=request.user,
            game_session=session,
            is_host=True
        )

    resp = {
         'code': session.code,
         'status': session.status,
         'round_length': session.round_length,
         'round_count': session.round_count,
         }
    
    if request.user and request.user.is_authenticated:
        resp.update({
            'participant_id': participant.id,
            'secret': participant.secret,
            'is_host': participant.is_host,
        })
        
    return Response(resp)

@api_view(['POST'])
@permission_classes([AllowAny])
def join_room(request):
    code = request.data.get('code', '').strip()
    if not code:
        return Response({'error': 'Kambario kodas privalomas.'}, status=400)
    try:
        session = GameSession.objects.get(code=code)
    except GameSession.DoesNotExist:
        return Response({'error': 'Kambarys su tokiu kodu neegzistuoja.'}, status=404)

    participant = None
    participant_id = request.data.get('participant_id')
    provided_secret = request.data.get('secret', '').strip()

    # 1) If user is logged in and NO credentials passed, auto-join or rejoin by User:
    if request.user and request.user.is_authenticated and not participant_id:
        participant, created = Participant.objects.get_or_create(
            user=request.user,
            game_session=session,
            defaults={'is_host': session.participants.count() == 0}
        )
        # On first join, if no question collections set, grab them all
        if created and session.question_collections.count() == 0:
            all_cols = QuestionCollection.objects.filter(is_deleted=False)
            session.question_collections.set(all_cols)
            session.save()

    # 2) Reconnect flow if participant_id & secret supplied:
    if not participant and participant_id and provided_secret:
        try:
            participant = session.participants.get(id=participant_id)
            if participant.secret != provided_secret:
                return Response({'error': 'Netinkamas slaptažodis.'}, status=403)
        except Participant.DoesNotExist:
            return Response({'error': 'Dalyvis nerastas.'}, status=404)

    # 3) Guest/new-join
    if not participant:
        # only allow joins in pending 
        if session.status != 'pending':
            return Response({'error': 'Žaidimas jau prasidėjo arba baigėsi.'}, status=400)

        user = request.user if request.user.is_authenticated else None
        guest_username = None if user else request.data.get('guest_username', '').strip()
        name_to_join = user.username if user else guest_username
        if not name_to_join:
            return Response({'error': 'Prašome įvesti vartotojo vardą.'}, status=400)

        # duplicate‐name check
        existing_names = []
        for p in session.participants.all():
            if p.user and p.user.username:
                existing_names.append(p.user.username.lower())
            elif p.guest_name:
                existing_names.append(p.guest_name.lower())
        if name_to_join.lower() in existing_names:
            return Response(
                {'error': 'Toks vartotojo vardas jau naudojamas kambaryje.'},
                status=400
            )

        is_host = (session.participants.count() == 0)
        if user:
            participant, _ = Participant.objects.get_or_create(
                user=user,
                game_session=session,
                defaults={'is_host': is_host}
            )
        else:
            import uuid
            participant = Participant.objects.create(
                guest_identifier=str(uuid.uuid4()),
                guest_name=guest_username,
                game_session=session,
                is_host=is_host
            )
        # assign collections on first join
        if session.question_collections.count() == 0:
            session.question_collections.set(QuestionCollection.objects.all())
            session.save()

    # Broadcast and build the response payload
    broadcast_lobby_update(session)

    players = []
    for p in session.participants.all().order_by('joined_at'):
        players.append({
            'id': p.id,
            'username': p.user.username if p.user else p.guest_name,
            'characterSelected': p.assigned_character is not None,
            'is_host': p.is_host,
        })

    messages = []
    for msg in Message.objects.filter(round__game_session=session).order_by('sent_at'):
        if msg.participant and msg.participant.assigned_character:
            char = msg.participant.assigned_character
            character_image = char.image.url if char.image else None
            character_name = char.name
        else:
            character_image = None
            character_name = "System" if msg.message_type == "system" else None
        messages.append({
            'id': msg.id,
            'text': msg.text,
            'sentAt': msg.sent_at.isoformat(),
            'roundNumber': msg.round.round_number,
            'system': msg.message_type == 'system',
            'characterImage': character_image,
            'characterName': character_name,
        })

    collections_list = list(session.question_collections.filter(is_deleted=False).values('id', 'name'))

    current_round = None
    if session.status == 'in_progress':
        cur = session.rounds.filter(end_time__gt=timezone.now()).order_by('-round_number').first()
        if cur:
            current_round = {
                'round_number': cur.round_number,
                'question': cur.question.text if cur.question else '',
                'end_time': cur.end_time.isoformat(),
            }

    return Response({
        'code': session.code,
        'status': session.status,
        'round_length': session.round_length,
        'round_count': session.round_count,
        'guess_timer': session.guess_timer,
        'guess_deadline': session.guess_deadline.isoformat() if session.guess_deadline else None,
        'players': players,
        'participant_id': participant.id,
        'secret': participant.secret,
        'is_host': participant.is_host,
        'current_round': current_round,
        'messages': messages,
        'question_collections': collections_list
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def update_settings(request):
    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    provided_secret = request.data.get('secret', '').strip()
    round_length = request.data.get('round_length')
    round_count = request.data.get('round_count')
    guess_timer = request.data.get('guess_timer')

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
         return Response({'error': 'Neteisingi raundų nustatymų duomenys.'}, status=400)

    if guess_timer is not None:
         try:
             guess_timer = int(guess_timer)
             if guess_timer <= 0 or guess_timer > 600:
                 raise ValueError
         except (ValueError, TypeError):
             return Response({'error': 'Neteisingi spėjimų laiko nustatymo duomenys.'}, status=400)
         session.guess_timer = guess_timer

    session.round_length = round_length
    session.round_count = round_count

    # If selected collections were sent in the request, update them. 
    selected_ids = request.data.get('selectedCollections')
    if selected_ids is not None:
        # Assuming selected_ids is a list of collection ids.
        valid_collections = QuestionCollection.objects.filter(id__in=selected_ids, is_deleted=False)
        session.question_collections.set(valid_collections)

    session.save()

    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)
    
    return Response({
         'code': session.code,
         'status': session.status,
         'round_length': session.round_length,
         'round_count': session.round_count,
         'guess_timer': session.guess_timer,
         'question_collections': list(session.question_collections.values('id', 'name'))
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

    if session.status == 'pending':
         participant.delete()
    else:
         participant.is_active = False
         participant.save()

    remaining = session.participants.filter(is_active=True)
    if remaining.exists():
         # If the leaving participant was the host, assign host privileges to the oldest active participant.
         if was_host:
             oldest = remaining.order_by('joined_at').first()
             oldest.is_host = True
             oldest.save()
         from .utils import broadcast_lobby_update
         broadcast_lobby_update(session)
         return Response({'message': 'Išėjote iš kambario.'})
    else:
         # If no active participants remain and the session is pending, delete the session.
         # For non-pending sessions (i.e. ongoing or completed), you may prefer to keep the session
         # so that the game results remain visible.
         if session.status == 'pending':
             session.delete()
             return Response({'message': 'Išėjote iš kambario.'})
         else:
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
    valid_collections = QuestionCollection.objects.filter(id__in=collections_ids, is_deleted=False)
    # Update the session's question collections.
    session.question_collections.set(valid_collections)
    session.save()

    broadcast_lobby_update(session)

    collections_list = list(session.question_collections.values('id', 'name'))
    return Response({
         'code': session.code,
         'question_collections': collections_list,
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def available_collections(request):
    user = request.user if request.user.is_authenticated else None
    qs = QuestionCollection.objects.filter(
        Q(created_by=user) | Q(created_by__isnull=True),
        is_deleted=False
    ).values('id', 'name')
    return Response(list(qs))


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
        return Response({'error': 'Netinkas slaptažodis.'}, status=403)
    
    from .models import Character
    user = request.user if request.user.is_authenticated else None

    # Handle image upload, if provided.
    image = request.FILES.get('image')
    if image:
        # Validate that the file is an image.
        if not image.content_type.startswith('image/'):
            return Response({'error': 'Neteisingas failo tipas. Tinka .jpg, .png.'}, status=400)
        # Check file size (limit example: 5 MB)
        if image.size > 5 * 1024 * 1024:
            return Response({'error': 'Paveikslėlis per didelis. Didžiausias leidžiamas dydis yra 5MB.'}, status=400)
    
    new_character = Character.objects.create(
        name=name,
        description=description,
        creator=user,
        image=image
    )
    
    participant.assigned_character = new_character
    participant.save()
    
    from .utils import broadcast_lobby_update
    broadcast_lobby_update(session)
    
    return Response({'message': 'Personažas sukurtas ir pasirinktas.', 'character_id': new_character.id})


@api_view(['GET'])
@permission_classes([AllowAny])
def available_characters(request):
    user = request.user if request.user.is_authenticated else None
    characters = Character.objects.filter(
        Q(is_public=True)
        | Q(creator=user)
    ).values('id','name','description','image')
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
    
    live_cols = session.question_collections.filter(is_deleted=False)
    total_questions = sum(
        collection.questions.filter(is_deleted=False).count()
        for collection in live_cols
    )
    if total_questions < session.round_count:
         return Response({'error': 'Klausimų kolekcijose nepakanka klausimų pagal nurodytą raundų skaičių.'}, status=400)

    # All checks passed; change game status.
    session.status = 'in_progress'
    session.save()

    # Create the first round.
    round_number = 1
    start_time = timezone.now()
    end_time = start_time + timedelta(seconds=session.round_length)
    
    # Choose a random question from a random collection
    question = None
    if session.question_collections.exists():
        live_cols = session.question_collections.filter(is_deleted=False)
        if live_cols.exists():
            collections = list(live_cols)
        collection = random.choice(collections)
        questions = list(collection.questions.all())
        if questions:
            question = random.choice(questions)

    new_round = Round.objects.create(
        game_session=session,
        question=question,
        round_number=round_number,
        start_time=start_time,
        end_time=end_time
    )

    if question:
        send_system_message(
            new_round,
            f"<p><strong>{new_round.round_number} raundas</strong></p><p>{new_round.question.text if new_round.question else 'Nėra klausimo.'}</p>"
        )


    # Broadcast round update so clients can display the question, round number, and time left.
    broadcast_round_update(session.code, new_round)
    
    # Update lobby state for everyone.
    broadcast_lobby_update(session)
    
    return Response({
         'message': 'Žaidimas pradėtas.',
         'code': session.code,
         'status': session.status,
         'round_length': session.round_length,
         'round_count': session.round_count,
         'current_round': {
              'round_number': new_round.round_number,
              'question': new_round.question.text if new_round.question else '',
              'end_time': new_round.end_time.isoformat(),
         }
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def send_chat_message(request):
    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    secret = request.data.get('secret', '').strip()
    text = request.data.get('text', '').strip()

    if not code or not participant_id or not secret or not text:
        return Response({'error': 'Trūksta reikiamų laukų.'}, status=400)

    # Retrieve the game session
    try:
        session = GameSession.objects.get(code=code)
    except GameSession.DoesNotExist:
        return Response({'error': 'Nerasta žaidimo sesija.'}, status=404)

    # Only allow chat in "pending" or "in_progress" (example logic)
    if session.status not in ['pending', 'in_progress']:
        return Response({'error': 'Šios žaidimo stadijos metu žinučių siųsti negalima.'}, status=400)

    # Retrieve the participant
    try:
        participant = Participant.objects.get(id=participant_id, game_session=session)
    except Participant.DoesNotExist:
        return Response({'error': 'Dalyvis nerastas.'}, status=404)

    if participant.secret != secret:
        return Response({'error': 'Netinkamas slaptažodis.'}, status=403)

    current_round = session.rounds.filter(end_time__gt=timezone.now()).order_by('-round_number').first()
    if not current_round:
        return Response({'error': 'Palaukite sekančio raundo.'}, status=400)
    
    # Create the message in DB
    msg = Message.objects.create(
        participant=participant,
        round=current_round,
        text=text
    )

    # Broadcast the new message to the WebSocket group
    broadcast_chat_message(session.code, msg)

    return Response({'message': 'Žinutė išsiųsta.'})

@api_view(['GET'])
@permission_classes([AllowAny])
def available_guess_options(request):
    code = request.query_params.get('code', '').strip()
    participant_id = request.query_params.get('participant_id', '').strip()
    provided_secret = request.query_params.get('secret', '').strip()

    if not code or not participant_id or not provided_secret:
        return Response(
            {'error': 'Prašome įvesti kambario kodą, dalyvio ID ir slaptažodį.'},
            status=400
        )

    try:
        session = GameSession.objects.get(code=code)
    except GameSession.DoesNotExist:
        return Response({'error': 'Kambarys nerastas.'}, status=404)
    
    if session.status != 'guessing':
        return Response(
            {'error': 'Spėjimų pasirinkimai prieinami tik spėjimų fazėje.'},
            status=400
        )
    
    try:
        participant = session.participants.get(id=participant_id)
    except Participant.DoesNotExist:
        return Response({'error': 'Dalyvis nerastas.'}, status=404)
    
    if participant.secret != provided_secret:
        return Response({'error': 'Netinkamas slaptažodis.'}, status=403)

    assigned_chars = (
        session.participants
        .filter(assigned_character__isnull=False)
        .exclude(id=participant.id)
        .values('assigned_character__id', 'assigned_character__name', 'assigned_character__image')
        .distinct()
    )
    
    options = []
    for char in assigned_chars:
        image_url = char['assigned_character__image']
        if image_url and not image_url.startswith('/'):
            image_url = '/media/' + image_url
        options.append({
            'character_id': char['assigned_character__id'],
            'character_name': char['assigned_character__name'],
            'character_image': image_url if image_url else None
        })
    
    return Response(options)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_guesses(request):
    from .models import GameSession, Participant, Guess, Character

    code = request.data.get('code', '').strip()
    participant_id = request.data.get('participant_id')
    secret = request.data.get('secret', '').strip()
    guesses_data = request.data.get('guesses', [])

    # Validate session & participant
    try:
        session = GameSession.objects.get(code=code)
        participant = Participant.objects.get(id=participant_id, game_session=session)
    except (GameSession.DoesNotExist, Participant.DoesNotExist):
        return Response({'error': 'Neteisingas kambarys arba dalyvio ID.'}, status=404)

    if participant.secret != secret:
        return Response({'error': 'Netinkamas slaptažodis.'}, status=403)

    if session.status != 'guessing':
        return Response({'error': 'Šiuo metu negalima pateikti spėjimų (ne spėjimų fazė).'}, status=400)

    if session.guess_deadline and timezone.now() > session.guess_deadline:
        return Response({'error': 'Laikas spėjimams pasibaigė.'}, status=400)
    
    # Limit total guesses to (number_of_participants - 1)
    max_guesses = session.participants.count() - 1
    if len(guesses_data) > max_guesses:
        return Response({'error': 'Per daug spėjimų.'}, status=400)

    # Check for duplicates within the current submission
    guessed_participant_ids = set()
    for g in guesses_data:
        gp_id = g.get('guessed_participant_id')
        if not gp_id:
            return Response({'error': 'Trūksta guessed_participant_id lauko.'}, status=400)
        if gp_id == participant.id:
            return Response({'error': 'Negalite spėti savęs.'}, status=400)
        if gp_id in guessed_participant_ids:
            return Response({'error': 'Negalite spėti to paties dalyvio daugiau nei vieną kartą.'}, status=400)
        guessed_participant_ids.add(gp_id)

    # Get all character IDs that are valid in this session
    assigned_char_ids = set(
        session.participants
               .exclude(assigned_character=None)
               .values_list('assigned_character_id', flat=True)
    )

    updated_guesses = []
    for guess_info in guesses_data:
        gp_id = guess_info['guessed_participant_id']
        gc_id = guess_info.get('guessed_character_id')
        if not gc_id:
            return Response({'error': 'Trūksta guessed_character_id lauko.'}, status=400)

        # Validate the guessed participant
        try:
            guessed_participant = session.participants.get(id=gp_id)
        except Participant.DoesNotExist:
            return Response({'error': 'Neteisingas guessed_participant_id.'}, status=404)

        if not guessed_participant.assigned_character:
            return Response({'error': 'Šis dalyvis neturi priskirto personažo.'}, status=400)

        # Ensure the character belongs to this session
        if gc_id not in assigned_char_ids:
            return Response({'error': 'Šis personažas nepriklauso šiam kambariui.'}, status=400)

        # Determine if the guess is correct
        is_correct = (guessed_participant.assigned_character_id == gc_id)

        # Update existing guess only if the guessed character is different;
        # otherwise, if it doesn't exist, create it.
        try:
            guess = Guess.objects.get(guesser=participant, guessed_participant=guessed_participant)
            if guess.guessed_character_id != gc_id:
                guess.guessed_character_id = gc_id
                guess.is_correct = is_correct
                guess.save()
        except Guess.DoesNotExist:
            guess = Guess.objects.create(
                guesser=participant,
                guessed_participant=guessed_participant,
                guessed_character_id=gc_id,
                is_correct=is_correct
            )
        updated_guesses.append(guess.id)

    return Response({
        'message': 'Spėjimai sėkmingai pateikti.',
        'guesses_updated': updated_guesses
    })

