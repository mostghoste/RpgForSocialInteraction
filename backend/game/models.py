# game/models.py

from django.db import models
from django.contrib.auth.models import User

class Character(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='character_images/', null=True, blank=True)
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
        ('completed', 'Completed'),
    )
    code = models.CharField(max_length=20)
    # if the host user is deleted, the session record remains
    host = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='hosted_sessions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    round_length = models.IntegerField(default=60)  # Round duration in seconds.
    round_count = models.IntegerField(default=3)    # Total number of rounds for the session.

    # A session can reference one or several question collections.
    question_collections = models.ManyToManyField(
        'QuestionCollection', blank=True, related_name='game_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Session {self.code} ({self.status})"

class Participant(models.Model):
    # if the user is deleted, keep their participant record.
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='participants', null=True)
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

    def __str__(self):
        return f"Message from {self.participant.user.username} in round {self.round.round_number}"

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
        return (f"{self.guesser.user.username} guessed {self.guessed_character.name} "
                f"for {self.guessed_participant.user.username}")

