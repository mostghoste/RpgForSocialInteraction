# backend/game/tasks.py

import random
from openai import OpenAI
from celery import shared_task
from django.utils import timezone
from django.conf import settings

from .models import Round, Participant, Message, GameSession
from .utils import check_and_advance_rounds, broadcast_lobby_update, broadcast_chat_message

# instantiate the DeepSeek client once per worker
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
        from .scoring import compute_score_breakdown
        for participant in session.participants.all():
            breakdown, total = compute_score_breakdown(participant)
            participant.points = total
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
    npcs = session.participants.filter(
        is_npc=True, is_active=True, assigned_character__isnull=False
    )
    for npc in npcs:
        # enqueue generation + scheduling immediately
        npc_generate_and_schedule.delay(round_id, npc.id)

@shared_task
def npc_generate_and_schedule(round_id, participant_id):
    try:
        rnd = Round.objects.select_related('question','game_session').get(id=round_id)
        npc = Participant.objects.get(id=participant_id)
    except (Round.DoesNotExist, Participant.DoesNotExist):
        return

    # session = rnd.game_session

    # prev_rounds = Round.objects.filter(
    #     game_session=session,
    #     round_number__lt=rnd.round_number
    # ).order_by('round_number')

    # history_parts = []
    # for pr in prev_rounds:
    #     msgs = Message.objects.filter(round=pr, message_type='chat')
    #     for m in msgs:
    #         history_parts.append(
    #             f"Round {pr.round_number} – {m.participant.assigned_character.name}: {m.text}"
    #         )
    # history_context = "\n".join(history_parts)

    # Build prompt
    system_message = (
        "You are an AI participant in a role-playing game, fully immersed in your character.\n"
        "Never reveal you are an AI. You will produce three outputs:\n"
        "  1) A concise (1–2 sentence) answer *in English* from your character’s POV.\n"
        "  2) A *perfect* Lithuanian translation of that answer (no grammar or style errors).\n\n"
        "  3) A proofread translation with all grammar and style errors fixed.\n\n"
        f"Character Name: {npc.assigned_character.name}\n"
        f"Character Description: {npc.assigned_character.description}\n\n"
        "Tone: informal, a touch of humor. Speak in first person as your character.\n\n"
        "Formatting rules:\n"
        "- Your final output should ONLY be the fixed Lithuanian translation.\n"
        "- Do not use language that does not translate well, e.g. puns."
        "- Do NOT wrap your answers in quotes or add emojis.\n"
    )

    user_message = (
        f"Current question: \"{rnd.question.text}\"\n\n"
        "Answer the question in three parts (English, Lithuanian and proofread), but **only** return the final Lithuanian translation as your final output."
    )

    # Call DeepSeek
    try:
        resp = _client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user",   "content": user_message},
            ],
            temperature=1.3,
            stream=False
        )
        text = resp.choices[0].message.content.strip()
        if not text:
            print(f"[NPC {participant_id} | Round {round_id}] Empty response from DeepSeek, skipping.")
            return
    except Exception as e:
        print(f"[NPC {participant_id} | Round {round_id}] Error calling DeepSeek API:", e)
        return


    # Schedule broadcast to stagger npc responses
    now = timezone.now()
    remaining = (rnd.end_time - now).total_seconds()
    if remaining <= 0:
        print(
            f"[NPC {participant_id} | Round {round_id}] Dropped: "
            f"now={now.isoformat()}, end_time={rnd.end_time.isoformat()}"
        )
        return
    delay = random.uniform(0.2 * remaining, 0.8 * remaining)
    broadcast_npc_response.apply_async(
        args=(round_id, participant_id, text),
        countdown=delay
    )

@shared_task
def broadcast_npc_response(round_id, participant_id, text):
    try:
        rnd = Round.objects.select_related('game_session').get(id=round_id)
        npc = Participant.objects.get(id=participant_id)
    except (Round.DoesNotExist, Participant.DoesNotExist):
        print(f"[NPC {participant_id} | Round {round_id}] Could not find round or NPC.")
        return

    session = rnd.game_session
    now = timezone.now()
    if session.status != 'in_progress' or now >= rnd.end_time:
        print(
            f"[NPC {participant_id} | Round {round_id}] Dropped: "
            f"status={session.status}, now={now.isoformat()}, end_time={rnd.end_time.isoformat()}"
        )
        return

    msg = Message.objects.create(
        participant=npc,
        round=rnd,
        text=text,
        message_type='chat'
    )
    broadcast_chat_message(session.code, msg)
