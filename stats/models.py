from django.db import models

class Team(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    crest = models.URLField(null=True, blank=True)

class Player(models.Model):
    player_id = models.IntegerField(primary_key=True)
    team = models.ForeignKey(Team, related_name='players', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=50)
    nationality = models.CharField(max_length=50)
    image = models.URLField(null=True, blank=True)