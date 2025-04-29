# backend/game/tasks.py

import random
from openai import OpenAI
from celery import shared_task
from django.utils import timezone
from django.conf import settings

from .models import GameSession, Round, Participant, Message
from .utils import check_and_advance_rounds, broadcast_lobby_update, broadcast_chat_message

# instantiate once per worker
_client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL
)

@shared_task
def run_round_check():
    print("⏰ Celery: Checking rounds...")
    check_and_advance_rounds()

@shared_task
def run_game_end_check():
    now = timezone.now()
    sessions = GameSession.objects.filter(status='guessing', guess_deadline__lte=now)
    for session in sessions:
        print(f"Ending game for session {session.code}")
        for participant in session.participants.all():
            correct_guess_count = participant.guesses_made.filter(is_correct=True).count()
            points_from_guesses = correct_guess_count * 50
            rounds_with_messages = session.rounds.filter(messages__participant=participant).distinct().count()
            points_from_messages = rounds_with_messages * 100
            participant.points = points_from_guesses + points_from_messages
            participant.save()
        session.status = 'completed'
        session.save()
        broadcast_lobby_update(session)
    return "Game end check complete"

@shared_task
def schedule_npc_responses(round_id):
    try:
        rnd = Round.objects.get(id=round_id)
    except Round.DoesNotExist:
        return

    session = rnd.game_session
    now = timezone.now()
    time_left = (rnd.end_time - now).total_seconds()
    if time_left <= 0:
        return

    npcs = session.participants.filter(is_npc=True, is_active=True, assigned_character__isnull=False)
    for npc in npcs:
        # Pick a random delay between 20% and 80% of remaining round time
        delay = random.uniform(0.2 * time_left, 0.8 * time_left)
        generate_npc_response.apply_async((rnd.id, npc.id), countdown=delay)

@shared_task
def generate_npc_response(round_id, participant_id):
    try:
        rnd = Round.objects.select_related('question','game_session').get(id=round_id)
        npc = Participant.objects.get(id=participant_id)
    except (Round.DoesNotExist, Participant.DoesNotExist):
        return

    # use messages from other players for context
    existing_msgs = Message.objects.filter(round=rnd, participant__is_npc=False)
    context = "\n".join(
        f"{m.participant.assigned_character.name}: {m.text}"
        for m in existing_msgs
    )

    # build prompt
    system_message = (
        f"Tu esi AI dalyvis žaidime, kuriame visi žaidėjai vaidina veikėjus ir atsakinėja į klausimus.\n"
        f"Tavo veikėjo vardas: „{npc.assigned_character.name}“\n"
        f"Tavo veikėjo aprašymas: {npc.assigned_character.description}\n"
        f"Klausimas į kurį privalai atsakyti: {rnd.question.text}\n"
        f"Tau reikia lietuviškai atsakyti į pateiktą klausimą vaidinant paskirtą veikėją. Žaidimas veikia kaip turingo testas - gausi papildomų taškų, jei žaidėjai neatpažins, kad tu esi AI. Atsižvelk į kitų žaidėjų žinutes, kad tavo atsakymai per daug neišsišoktų."
    )
    user_message = (
        f"Kitų veikėjų, dalyvaujančių šiame žaidime, atsakymai į klausimą:"
        f"{context}\n\n"
    )

    # call DeepSeek
    try:
        resp = _client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user",   "content": user_message},
            ],
            stream=False
        )
    except Exception as e:
        print(f"[NPC {npc.id} | Round {rnd.id}] Error calling DeepSeek API:", e)
        return

    # pull out the text
    text = resp.choices[0].message.content.strip() or "(🤖 NPC nerado atsakymo)"

    # save & broadcast
    msg = Message.objects.create(
        participant=npc,
        round=rnd,
        text=text,
        message_type='chat'
    )
    broadcast_chat_message(rnd.game_session.code, msg)