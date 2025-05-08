# game/models.py

import uuid, os
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

def get_character_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    # Generate unique filename using uuid4
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("character_images", new_filename)

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class SoftDeleteModel(models.Model):
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    objects     = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

class Character(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=get_character_image_upload_path, null=True, blank=True)
    # When a creator is deleted dont delete character
    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_characters'
    )
    is_public = models.BooleanField(
        default=False,
        help_text="True for seeded/public characters, False for user-private ones"
    )
    ai_context = models.TextField(
        blank=True,
        default='',
        help_text="Additional context for AI participants"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class GameSession(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('guessing', "Guessing"),
        ('completed', 'Completed'),
    )
    code = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    round_length = models.IntegerField(default=60)  # Round duration in seconds
    round_count = models.IntegerField(default=3)    # Total number of rounds for the session
    guess_timer = models.IntegerField(default=60)  # Timer (in seconds) for guessing phase
    guess_deadline = models.DateTimeField(null=True, blank=True) # Deadline for submitting guesses
    npc_sequence = models.PositiveIntegerField(default=0) # NPC name id
    question_collections = models.ManyToManyField(
        'QuestionCollection', blank=True, related_name='game_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Session {self.code} ({self.status})"

def generate_secret():
    return uuid.uuid4().hex

class Participant(models.Model):
    # if user is deleted keep their participant
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='participants', null=True, blank=True)
    guest_identifier = models.CharField(max_length=36, null=True, blank=True)
    guest_name = models.CharField(max_length=50, null=True, blank=True)
    # if the session is deleted, remove all its participants
    game_session = models.ForeignKey(
        GameSession, on_delete=models.CASCADE, related_name='participants'
    )
    # if the character is deleted, set assigned_character to NULL
    assigned_character = models.ForeignKey(
        Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='participants'
    )
    points = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    secret = models.CharField(max_length=64, default=generate_secret)
    is_host = models.BooleanField(default=False)
    is_npc = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'game_session'],
                condition=models.Q(user__isnull=False),
                name='unique_user_session'
            ),
            models.UniqueConstraint(
                fields=['guest_identifier', 'game_session'],
                condition=models.Q(user__isnull=True),
                name='unique_guest_session'
            )
        ]

    def __str__(self):
        if self.user:
            username = self.user.username
        elif self.guest_name:
            username = self.guest_name
        elif self.guest_identifier:
            username = f"Guest {self.guest_identifier[:8]}"
        else:
            username = "Guest"
        if self.is_npc:
            username += " 🤖"
        return f"{username} in session {self.game_session.code}"

class Question(SoftDeleteModel):
    text = models.TextField()
    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_questions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def delete(self, using=None, keep_parents=False):
        # Has this question been asked in an active session?
        from .models import Round, QuestionCollection
        in_active_round = Round.objects.filter(
            question=self,
            game_session__status__in=['in_progress','guessing']
        ).exists()

        # Does it live in any collection used by an active session?
        in_active_collection = QuestionCollection.objects.filter(
            questions=self,
            game_sessions__status__in=['in_progress','guessing']
        ).exists()

        if in_active_round or in_active_collection:
            raise ValidationError(
                "Negalite ištrinti šio klausimo, jis naudojamas vykstančiame žaidime."
            )
        return super().delete(using=using, keep_parents=keep_parents)

    def save(self, *args, **kwargs):
        # Same checks for edits
        from .models import Round, QuestionCollection
        if self.pk:
            in_active_round = Round.objects.filter(
                question=self,
                game_session__status__in=['in_progress','guessing']
            ).exists()
            in_active_collection = QuestionCollection.objects.filter(
                questions=self,
                game_sessions__status__in=['in_progress','guessing']
            ).exists()

            if in_active_round or in_active_collection:
                raise ValidationError(
                    "Negalite keisti šio klausimo, jis naudojamas vykstančiame žaidime."
                )
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.text[:50]

class QuestionCollection(SoftDeleteModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    questions = models.ManyToManyField(Question, blank=True, related_name='collections')
    # When user who created the collection is deleted, set to NULL
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='question_collections'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def delete(self, using=None, keep_parents=False):
        if self.game_sessions.filter(status__in=['in_progress','guessing']).exists():
            raise ValidationError(
                "Negalite ištrinti klausimų kolekcijos, kuri naudojama vykstančiame žaidime."
            )
        return super().delete(using=using, keep_parents=keep_parents)

    def save(self, *args, **kwargs):
        if self.pk and self.game_sessions.filter(status__in=['in_progress','guessing']).exists():
            raise ValidationError(
                "Negalite keisti klausimų kolekcijos, kuri naudojama vykstančiame žaidime."
            )
        return super().save(*args, **kwargs)

class Round(models.Model):
    game_session = models.ForeignKey(
        GameSession, on_delete=models.CASCADE, related_name='rounds'
    )
    # prevent deletion of a question if its used in a round
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    round_number = models.PositiveIntegerField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('game_session', 'round_number')

    def __str__(self):
        return f"Round {self.round_number} in session {self.game_session.code}"

class Message(models.Model):
    participant = models.ForeignKey(
        Participant, on_delete=models.SET_NULL, related_name='messages', null=True
    )
    round = models.ForeignKey(
        Round, on_delete=models.CASCADE, related_name='messages'
    )
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    MESSAGE_TYPE_CHOICES = (
        ('chat', 'Chat'),
        ('system', 'System'),
    )
    message_type = models.CharField(
        max_length=10, choices=MESSAGE_TYPE_CHOICES, default='chat'
    )

    def __str__(self):
        if self.message_type == 'system':
            return f"System Message: {self.text[:50]}"
        if self.participant:
            if self.participant.user:
                name = self.participant.user.username
            elif self.participant.guest_name:
                name = self.participant.guest_name
            elif self.participant.guest_identifier:
                name = f"Guest {self.participant.guest_identifier[:8]}"
            else:
                name = "Guest"
        else:
            name = "Unknown"
        return f"Message from {name} in round {self.round.round_number}"


class Guess(models.Model):
    # Participant making the guess (spėjikas)
    guesser = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='guesses_made'
    )
    # Participant who is being guessed (spėjamasis)
    guessed_participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='guesses_received'
    )
    # The character being guessed
    guessed_character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='guesses'
    )
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.guesser:
            if self.guesser.user:
                guesser_name = self.guesser.user.username
            elif self.guesser.guest_name:
                guesser_name = self.guesser.guest_name
            elif self.guesser.guest_identifier:
                guesser_name = f"Guest {self.guesser.guest_identifier[:8]}"
            else:
                guesser_name = "Guest"
        else:
            guesser_name = "Unknown"

        if self.guessed_participant:
            if self.guessed_participant.user:
                guessed_participant_name = self.guessed_participant.user.username
            elif self.guessed_participant.guest_name:
                guessed_participant_name = self.guessed_participant.guest_name
            elif self.guessed_participant.guest_identifier:
                guessed_participant_name = f"Guest {self.guessed_participant.guest_identifier[:8]}"
            else:
                guessed_participant_name = "Guest"
        else:
            guessed_participant_name = "Unknown"

        return f"{guesser_name} guessed {self.guessed_character.name} for {guessed_participant_name}"