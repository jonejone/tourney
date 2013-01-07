from django.db import models
from django.contrib.auth.models import User


class PlayerClass(models.Model):
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return self.name


class Tournament(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    user = models.ForeignKey(User)
    classes = models.ManyToManyField(PlayerClass)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return self.name


class Player(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)

    pdga_number = models.PositiveIntegerField(
        verbose_name='PDGA Number',
        blank=True,
        null=True)

    user = models.ForeignKey(User,
        blank=True, null=True)

    phonenumber = models.CharField(max_length=20,
        blank=True, null=True)


class TournamentPlayer(models.Model):
    player = models.ForeignKey(Player)
    player_class = models.ForeignKey(PlayerClass)
    tournament = models.ForeignKey(Tournament)
    registered = models.DateTimeField()
    is_paid = models.BooleanField()



