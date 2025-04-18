# game/models.py

import uuid, os
from django.db import models
from django.contrib.auth.models import User

def get_character_image_upload_path(instance, filename):
    # Extract the file extension
    ext = filename.split('.')[-1]
    # Generate a unique filename using uuid4
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    # Return the full path where the file will be stored
    return os.path.join("character_images", new_filename)

class Character(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=get_character_image_upload_path, null=True, blank=True)
    # When a creator (User) is deleted, set field to NULL (Don't delete the character).
    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_characters'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Set once at creation.
    updated_at = models.DateTimeField(auto_now=True)  # Updated on each save.

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
    round_length = models.IntegerField(default=60)  # Round duration in seconds.
    round_count = models.IntegerField(default=3)    # Total number of rounds for the session.
    guess_timer = models.IntegerField(default=60)  # Timer (in seconds) for guessing phase.
    guess_deadline = models.DateTimeField(null=True, blank=True) # Deadline for submitting guesses.

    # A session can reference one or several question collections.
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
    # if the user is deleted, keep their participant record.
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='participants', null=True, blank=True)
    guest_identifier = models.CharField(max_length=36, null=True, blank=True)
    guest_name = models.CharField(max_length=50, null=True, blank=True)
    # if the session is deleted, remove all its participants.
    game_session = models.ForeignKey(
        GameSession, on_delete=models.CASCADE, related_name='participants'
    )
    # if the character is deleted, set assigned_character to NULL.
    assigned_character = models.ForeignKey(
        Character, on_delete=models.SET_NULL, null=True, blank=True, related_name='participants'
    )
    points = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    secret = models.CharField(max_length=64, default=generate_secret)
    is_host = models.BooleanField(default=False)

    class Meta:
        constraints = [
            # For authenticated users, ensure a user can join a session only once.
            models.UniqueConstraint(
                fields=['user', 'game_session'],
                condition=models.Q(user__isnull=False),
                name='unique_user_session'
            ),
            # For guest users, use guest_identifier to ensure uniqueness within a session.
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
        return f"{username} in session {self.game_session.code}"

class Question(models.Model):
    text = models.TextField()
    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_questions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]

class QuestionCollection(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    questions = models.ManyToManyField(Question, blank=True, related_name='collections')
    # When a user who created the collection is deleted, set this to NULL.
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='question_collections'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Round(models.Model):
    game_session = models.ForeignKey(
        GameSession, on_delete=models.CASCADE, related_name='rounds'
    )
    # prevent deletion of a question if it’s used in a round.
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
    # The participant making the guess.
    guesser = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='guesses_made'
    )
    # The participant who is being guessed (matched to the role).
    guessed_participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='guesses_received'
    )
    # The character (role) being guessed.
    guessed_character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='guesses'
    )
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Determine guesser name
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

        # Determine guessed participant name
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