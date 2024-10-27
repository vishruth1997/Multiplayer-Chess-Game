from django.db import models
from django.contrib.auth.models import User

class Board(models.Model):
    location = models.CharField(max_length=11)
    value = models.CharField(max_length=10)
    user =  models.ForeignKey(User, on_delete=models.CASCADE)
    fen = models.CharField(max_length=100, null=True, blank=True)  

    class Meta:
        unique_together = (("user", "location"))

class Game(models.Model):
    player1 = models.ForeignKey(User, related_name='player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='player2', on_delete=models.CASCADE)
    moves = models.IntegerField(default=0)
    outcome = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    fen = models.CharField(max_length=100, default='startpos')  # Store FEN for both players
    turn = models.CharField(max_length=5, default='white')  # Store whose turn it is ('white' or 'black')

    # New field to track users who have deleted the game
    deleted_by = models.ManyToManyField(User, related_name='deleted_games', blank=True)

    def is_player_turn(self, user):
        """Check if it's the user's turn."""
        if self.turn == 'white' and user == self.player1:
            return True
        elif self.turn == 'black' and user == self.player2:
            return True
        return False
    
# New model to store journal entries specific to each user for each game
class UserGameJournal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    journal_entry = models.TextField(blank=True, null=True)
    deleted_for_user = models.BooleanField(default=False)  # New field to track deletion

    class Meta:
        unique_together = (("user", "game"))

