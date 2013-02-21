from django.test import TestCase
from django.utils.timezone import utc
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.timezone import now

from datetime import datetime, date, timedelta

from .models import (Tournament, Player, PlayerClass,
                     RegistrationStage,
                     TournamentClassPrice,
                     TournamentSite,
                     RegistrationStageClass,)


def generate_user():
    try:
        user = User.objects.all()[0]
    except:
        user = User.objects.create_user(
            'test', 'foo@bar.com', 'foo')

    return user

def generate_site():
    return Site.objects.create(
        domain='testserver',
        name='testserver')

def generate_tournament(user=None):

    if not user:
        user = generate_user()

    create_kwargs = {
        'name': 'Some tournament',
        'slug': 'some-tournament',
        'currency': 'NOK',
        'user': user,
        'registration_stages': False,
    }

    # Set start and end dates to 4 weeks
    # in the future
    create_kwargs.update({
        'start_date': date.today() + timedelta(weeks=4),
        'end_date': date.today() + timedelta(weeks=5),
    })

    # Set registration start times, by default
    # we set registration to be open currently
    create_kwargs.update({
        'registration_opens': now() - timedelta(days=7),
        'registration_ends': now() + timedelta(days=7),
    })

    # Create the tournament
    tournament = Tournament.objects.create(
        **create_kwargs)

    # Now we need to setup some player classes
    player_classes = generate_player_classes()
    tournament.classes = player_classes

    # Setup player class costs
    return tournament


def generate_player_classes():
    return [PlayerClass.objects.create(name=x) for x in
        ['open', 'women', 'amateur', 'masters',]]


class TournamentTestCase(TestCase):
    def setUp(self):
        self.user = generate_user()
        self.tournament = generate_tournament(user=self.user)
        self.site = generate_site()

        # Set up tournament site
        ts = TournamentSite.objects.create(
            tournament=self.tournament,
            site=self.site)


class TournamentAnalyticsTest(TournamentTestCase):
    def test_analytics(self):
        u = 'UA-SOMEACCOUNTCODE'
        t = self.tournament
        t.google_analytics_account = u
        t.save()

        r = self.client.get('/')

        # Make sure that our custom Google Analytics code
        # is part of the markup at the rendered page
        self.assertTrue(u in r.content)


class TournamentMaxPlayersTest(TournamentTestCase):
    def setUp(self, *kargs, **kwargs):
        super(TournamentMaxPlayersTest, self).setUp(
            *kargs, **kwargs)

        self.tournament.max_players = 100
        self.tournament.wildcard_spots = 20

    def test_available_spots(self):
        self.assertEqual(
            80, self.tournament.get_available_spots())

        # Now lets register a player to see if
        # new available spots becomes 79
        player_class = self.tournament.classes.all()[0]

        r = self.client.post(
            '/registration/',
            {
                'name': 'Tester',
                'country': 'NO',
                'pdga_terms': True,
                'player_class': player_class.id
            }
        )

        # Just check that it went as expected
        self.assertEqual(r.status_code, 302)

        self.assertEqual(
            79, self.tournament.get_available_spots())

        # Lets reduce wildcard_spots by one
        self.tournament.wildcard_spots = 19

        # Then it should be 80 open again
        self.assertEqual(
            80, self.tournament.get_available_spots())


class RegistrationOpenTest(TournamentTestCase):
    def test_open_default(self):
        t = self.tournament
        self.assertTrue(t.is_registration_open())

    def test_closed_before(self):
        t = self.tournament

        # Set the registration to start tomorrow
        t.registration_opens = now() + timedelta(days=1)
        self.assertEqual(False, t.is_registration_open())

    def test_closed_after(self):
        t = self.tournament

        # Set the registration to be finished
        t.registration_opens = now() - timedelta(days=5)
        t.registration_ends = now() - timedelta(days=3)

        self.assertEqual(
            False,
            t.is_registration_open())

    def test_closed_five_seconds_ago(self):
        t = self.tournament
        t.registration_ends = now() - timedelta(seconds=5)

        self.assertEqual(
            False,
            t.is_registration_open())

    def test_closes_in_five_seconds(self):
        t = self.tournament
        t.registration_ends = now() + timedelta(seconds=5)

        self.assertTrue(t.is_registration_open())

    def test_opens_in_five_seconds(self):
        t = self.tournament
        t.registration_opens = now() + timedelta(seconds=5)

        self.assertEqual(False, t.is_registration_open())


class EmbedTest(TournamentTestCase):
    def test_players(self):
        t = self.tournament
        r = self.client.get('/registration/embed/')

        # Make sure our embed version contains
        # embed-wrapper class name
        self.assertTrue(
            'embed-wrapper' in r.content)

    def test_registration(self):
        t = self.tournament
        r = self.client.get('/players/embed/')

        # Make sure our embed version contains
        # embed-wrapper class name
        self.assertTrue(
            'embed-wrapper' in r.content)


class RegisterPlayerTest(TournamentTestCase):
    def test_get_register_player(self):
        t = self.tournament
        r = self.client.get('/registration/')

        # Make sure we can see the form fields,
        # meaning registration is "open"
        self.assertTrue('id_pdga_number' in r.content)

    def test_post_register_player(self):
        t = self.tournament

        initial_player_count = t.tournamentplayer_set.count()
        player_class = self.tournament.classes.all()[0]

        r = self.client.post(
            '/registration/',
            {
                'name': 'Tester',
                'country': 'NO',
                'pdga_terms': True,
                'player_class': player_class.id
            }
        )

        self.assertEqual(r.status_code, 302)

        # Make sure player count increased by one
        self.assertEqual(
            t.tournamentplayer_set.count(),
            initial_player_count+1)
