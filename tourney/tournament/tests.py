from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import now

from datetime import datetime, date, timedelta

from .models import (Tournament, Player, PlayerClass,
                     RegistrationStage,
                     TournamentClassPrice,
                     RegistrationStageClass,)


def generate_tournament():
    try:
        user = User.objects.all()[0]
    except:
        user = User.objects.create_user(
            'test', 'foo@bar.com', 'foo')

    return Tournament.objects.create(
        name='Sula Open 2013',
        slug='sula-open-2013',
        user=user,
        start_date=date.today(),
        registration_stages=True,
        currency='NOK',
        tournament_admin_email='foo@example.com')


def generate_player_classes():
    for i in ['open', 'women', 'amateur',
              'masters', 'grandmasters']:

        PlayerClass.objects.create(name=i)


def generate_registration_stages(t, num=4):
    start_rating = 950
    rating_increments = 50

    for x in range(num):
        stage = RegistrationStage(
            tournament=t,
            opens=datetime.now())

        stage.save()

        required_rating = start_rating - (
            rating_increments * x)

        for class_ in t.classes.all():
            stage_class = RegistrationStageClass(
                registration_stage=stage,
                player_class=class_,
                rating_required=required_rating)

            stage_class.save()


def generate():
    t = generate_tournament()
    generate_player_classes()
    generate_registration_stages(t, 3)


class RegisterPlayerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'foo@bar.com', 'foo')

        self.tournament = Tournament.objects.create(
            name='Some tournament',
            slug='foo',
            user=self.user,
            start_date=date.today() + timedelta(days=10))

        self.player_class = PlayerClass.objects.create(
            name='Some player class')

        self.tournament.registration_stages = False

        # Registration openeed yesterday
        self.tournament.registration_opens = (
            now() -
            timedelta(days=1))

        # Registration closes tomorrow
        self.tournament.registration_ends = (
            now() +
            timedelta(days=1))

        self.tournament.save()
        self.tournament.classes = [self.player_class, ]

        # Set up registration costs
        TournamentClassPrice.objects.create(
            tournament=self.tournament,
            player_class=self.player_class,
            price=500)

    def test_post_register_player(self):

        r = self.client.post(
            '/registration/',
            {
                'name': 'Tester',
                'country': 'NO',
                'pdga_terms': True,
                'player_class': self.player_class.id
            }
        )

        self.assertEqual(r.status_code, 302)

        self.assertEqual(
            r['location'],
            'http://testserver/registration-complete/')

        self.assertEqual(Player.objects.count(), 1)

    def test_get_register_player(self):
        r = self.client.get('/registration/')

        self.assertEqual(r.status_code, 200)
        self.assertTrue('id_pdga_number' in r.content)
