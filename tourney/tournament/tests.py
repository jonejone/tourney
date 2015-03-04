#-*-coding: utf8
from django.utils import simplejson
from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.utils.timezone import utc
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.timezone import now

from mock import patch
from StringIO import StringIO
from datetime import datetime, date, timedelta
from nose.plugins.attrib import attr

from .utils.pdga import PDGARanking
from .forms import RegistrationForm, TournamentForm
from .models import (Tournament, Player, PlayerClass,
                     RegistrationStage,
                     TournamentClassPrice,
                     TournamentOption,
                     TournamentSite,
                     TournamentPlayer,
                     RegistrationStageClass,)


def generate_tournament_player(tournament):
    player_class = tournament.classes.all()[0]
    create_kwargs = {
        'player': generate_player(),
        'player_class': player_class,
        'tournament': tournament,
        'registered': now(),
    }

    if tournament.get_available_spots() < 1:
        create_kwargs.update({'is_waiting_list': True})

    return TournamentPlayer.objects.create(**create_kwargs)


def generate_player():
    player_kwargs = {
        'name': 'Some player name',
    }

    player = Player.objects.create(
        **player_kwargs)

    player.email = 'player%i@example.com' % player.id
    player.save()

    return player


def generate_user():
    user = User.objects.create_user(
        'test', 'foo@bar.com', 'password')

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
        'tournament_admin_email': 'tourney@admin.com',
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


def generate_tournament_class_prices(tournament):
    return [TournamentClassPrice.objects.create(
        tournament=tournament,
        player_class=player_class,
        price=100) for player_class in tournament.classes.all()]

def generate_tournament_options(tournament):
    return [TournamentOption.objects.create(
        name=x,
        price=100,
        tournament=tournament) for x in
            ['Lodging', 'Dinner saturday', 'Breakfast']]


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

        # Add some config
        self.tournament.currency_code = 'NOK'

        generate_tournament_class_prices(self.tournament)


class WaitingListTestCase(TournamentTestCase):
    def setUp(self, *kargs, **kwargs):

        super(WaitingListTestCase, self).setUp(
            *kargs, **kwargs)

        self.tournament.max_players = 1
        self.tournament.wildcard_spots = 0

        generate_tournament_player(self.tournament)
        generate_tournament_player(self.tournament)


class TournamentAdminTestCase(TournamentTestCase):
    def setUp(self):
        super(TournamentAdminTestCase, self).setUp()

        # First we must login
        user = self.client.login(
            username=self.user.username,
            password='password')

        # Now we must make this user an admin
        self.tournament.tournamentadmin_set.create(
            user=self.user)


class TournamentPlayerActionTestCase(TournamentAdminTestCase):
    def setUp(self, *kargs, **kwargs):
        super(TournamentPlayerActionTestCase, self).setUp(
            *kargs, **kwargs)

        # Add some players and settings
        self.tournament.max_players = 1
        self.tournament.wildcard_spots = 0

        generate_tournament_player(self.tournament)
        generate_tournament_player(self.tournament)

        # Add a spot so there is one available
        self.tournament.max_players += 1
        self.tournament.save()

    def test_remove_player(self):
        t = self.tournament

        player = self.tournament.tournamentplayer_set.filter(
            is_waiting_list=True)[0]

        self.assertEqual(
            t.get_waiting_list_count(), 1)

        player_count_before = t.get_player_list_count()

        post_data = {
            'tournamentplayer_id': player.id,
            'action': 'waiting-list-remove',
        }

        r = self.client.post('/ajax/player-action/', post_data)

        # Check JSON response
        json_response = simplejson.loads(r.content)

        self.assertEqual(
            json_response['success'], True)

        # Make sure we got a 200 response
        self.assertEqual(
            r.status_code,
            200)

        # Now there shouldn't be anyone on waiting list
        self.assertEqual(
            t.get_waiting_list_count(), 0)

        # The players count should stay the same
        self.assertEqual(
            t.get_player_list_count(),
            player_count_before)

    def test_accept_player(self):
        t = self.tournament

        player = self.tournament.tournamentplayer_set.filter(
            is_waiting_list=True)[0]

        self.assertEqual(
            t.get_waiting_list_count(), 1)

        player_count_before = t.get_player_list_count()

        post_data = {
            'tournamentplayer_id': player.id,
            'action': 'waiting-list-accept',
        }

        r = self.client.post('/ajax/player-action/', post_data)

        # Make sure we got a 200 response
        self.assertEqual(
            r.status_code,
            200)

        # Check JSON response
        json_response = simplejson.loads(r.content)

        self.assertEqual(
            json_response['success'], True)


        # Now there shouldn't be anyone on waiting list
        self.assertEqual(
            t.get_waiting_list_count(), 0)

        # Make sure players count increased by one
        self.assertEqual(
            t.get_player_list_count(),
            player_count_before + 1)


class TournamentMailPlayersTestCase(TournamentAdminTestCase):
    def setUp(self, *kargs, **kwargs):

        super(TournamentMailPlayersTestCase, self).setUp(
            *kargs, **kwargs)

        self.tournament.max_players = 5
        self.tournament.wildcard_spots = 0

        generate_tournament_player(self.tournament)
        generate_tournament_player(self.tournament)
        generate_tournament_player(self.tournament)
        generate_tournament_player(self.tournament)
        generate_tournament_player(self.tournament)
        generate_tournament_player(self.tournament)
        generate_tournament_player(self.tournament)

    @attr('include')
    def test_post(self):

        outbox_length = len(mail.outbox)

        post_data = {
            'email_player_list': True,
            'email_waiting_list': True,
            'sender': 'mail@example.com',
            'subject': 'Testing an email sending!',
            'body': 'This is my body'
        }

        r = self.client.post('/email-players/', post_data)

        # Check the status response
        self.assertEqual(r.status_code, 302)

        # Make sure our outbox has mail for all players
        self.assertTrue(
            len(mail.outbox) > outbox_length)

    def test_get(self):

        r = self.client.get('/email-players/')
        self.assertEqual(r.status_code, 200)

        # Make sure it contains a form
        self.assertTrue(
            '<form method="post" action="/email-players/"' in \
                r.content)

        # Make sure it displays correctly the amount of
        # players in the list, as well as waiting
        self.assertTrue(
            'accepted players (5)' in r.content)

        self.assertTrue(
            'waiting list (2)' in r.content)


class TournamentEditTestCase(TournamentAdminTestCase):
    def _test_edit_tournament_post(self):

        t = self.tournament

        # Create a form with our tournament
        form = TournamentForm(
            instance=t)

        post_data = form.initial
        post_data.update({'name': 'A new name'})

        r = self.client.post('/edit/', post_data)

    def test_edit_tournament_get(self):
        r = self.client.get('/edit/')
        self.assertEqual(r.status_code, 200)

        # Make sure it contains a form
        self.assertTrue(
            '<form method="post" action="/edit/"' in \
                r.content)


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


class TournamentOptionTestCase(TournamentTestCase):
    def test_available(self):
        t = self.tournament
        options = generate_tournament_options(
            tournament=t)

        form = RegistrationForm(tournament=t)

        # Lets take one of the options, make sure displays
        # properly in the form. Then, set "is_available" to
        # false, re-render form, and make sure the option
        # now is no longer available
        option = options[0]

        self.assertTrue(
            option.name in form.as_table())

        # Okay, time to make it unavailable
        option.is_available = False
        option.save()

        # Re-create form
        form = RegistrationForm(tournament=t)

        self.assertTrue(
            option.name not in form.as_table())

    def test_options(self):
        t = self.tournament

        # Lets set some options
        options = generate_tournament_options(tournament=t)
        form = RegistrationForm(tournament=t)

        # Now we have some options, make sure the field
        # is part of the form
        self.assertTrue(
            'options' in form.fields)

    def test_default(self):
        t = self.tournament
        form = RegistrationForm(tournament=t)

        # Default tournament doesnt have any options,
        # make sure multiplechoice field is not part of the form
        self.assertTrue(
            'options' not in form.fields)


class WaitingListEmailTest(WaitingListTestCase):
    def setUp(self, *kargs, **kwargs):

        super(WaitingListEmailTest, self).setUp(
            *kargs, **kwargs)

        self.tournament.tournament_admin_email = 'foo@bar.com'
        self.tournament.max_players = 10

        player = self.tournament.tournamentplayer_set.get(
            is_waiting_list=True)

        player.player.email = 'bar@foo.com'
        self.player = player

    def email_test(self):
        outbox_length_before = len(mail.outbox)
        self.player.accept_player()
        self.assertEqual(
            len(mail.outbox),
            outbox_length_before + 1)


"""
class ExportCommandTest(TournamentTestCase):
    @attr('include')
    def test_working(self):

        # Call the management command
        args = ['some-tournament', ]
        #opts = {'updatemissing': True}
        opts = {}

        with patch('sys.stdout', new_callable=StringIO) as stdout_mock:
            call_command('export', *args, **opts)
            import pdb
            pdb.set_trace()
"""

class PDGARankUtilTest(TestCase):
    @attr('include')
    @patch('tourney.tournament.utils.pdga.urlopen')
    def test_working(self, urlopen_mock):

        # Mock response from urlopen for PDGA lookup
        urlopen_mock.return_value = StringIO(pdga_response)

        pdga_number = '28903'
        pdga = PDGARanking(pdga_number)

        # Assure correct values based on our mock
        self.assertEqual(pdga.rating, 932)
        self.assertEqual(pdga.name, 'Jone Eide')


class PDGARankCommandTest(TournamentTestCase):
    @patch('tourney.tournament.utils.pdga.urlopen')
    def test_update_missing_invalid(self, urlopen_mock):
        t = self.tournament

        # Mock response from urlopen for PDGA lookup
        urlopen_mock.return_value = StringIO('Bad response!')

        # Lets generate a player player with PDGA number
        p1 = generate_tournament_player(t)
        p1.player.pdga_number = '28903'
        p1.player.save()

        # Call the management command
        args = ['some-tournament', ]
        opts = {'updatemissing': True}

        with patch('sys.stdout', new_callable=StringIO) as stdout_mock:
            call_command('pdgarank', *args, **opts)
            self.assertTrue(
                'unable to update %s' % (p1.player.name) \
                in stdout_mock.getvalue())

    @patch('tourney.tournament.utils.pdga.urlopen')
    def test_update_missing_none(self, urlopen_mock):
        t = self.tournament

        # Mock response from urlopen for PDGA lookup
        urlopen_mock.return_value = StringIO(pdga_response)

        # Call the management command
        args = ['some-tournament', ]
        opts = {'updatemissing': True}

        with patch('sys.stdout', new_callable=StringIO) as stdout_mock:
            call_command('pdgarank', *args, **opts)
            self.assertTrue(
                'No players to update' in stdout_mock.getvalue())

    @patch('tourney.tournament.utils.pdga.urlopen')
    def test_update_missing(self, urlopen_mock):
        t = self.tournament

        # Mock response from urlopen for PDGA lookup
        urlopen_mock.return_value = StringIO(pdga_response)

        # Lets generate a player player with PDGA number
        p1 = generate_tournament_player(t)
        p1.player.pdga_number = '28903'
        p1.player.save()

        # Call the management command
        args = ['some-tournament', ]
        opts = {'updatemissing': True}

        with patch('sys.stdout', new_callable=StringIO) as stdout_mock:
            call_command('pdgarank', *args, **opts)

            self.assertTrue(
                'Trying to update 1 players' in stdout_mock.getvalue())

        # Now make sure the player has a PDGA rating saved
        p = t.tournamentplayer_set.all()[0]

        self.assertEqual(p.player.pdga_rating, 1027)


class WaitingListCommandTest(WaitingListTestCase):
    def test_sync_command(self):
        players = self.tournament.tournamentplayer_set.filter(
            is_waiting_list=True)

        players_waiting_list_before = self.tournament.\
            get_waiting_list_count()

        players_list_before = self.tournament.\
            get_player_list_count()

        spots_before = self.tournament.get_available_spots()

        args = ['some-tournament']
        opts = {'accept': True}
        call_command('waitinglist', *args, **opts)

        # Make sure player list increased by one
        self.assertEqual(
            self.tournament.get_player_list_count(),
            players_waiting_list_before + 1)

        # Make sure waiting list count reduced by one
        self.assertEqual(
            self.tournament.get_waiting_list_count(),
            players_waiting_list_before - 1)

        # Make sure available spots reduced by one
        self.assertEqual(
            self.tournament.get_available_spots(),
            spots_before - 1)


    def test_sync_player_command(self):
        players = self.tournament.tournamentplayer_set.filter(
            is_waiting_list=True)

        player = players[0]

        players_waiting_list_before = self.tournament.\
            get_waiting_list_count()

        players_list_before = self.tournament.\
            get_player_list_count()

        spots_before = self.tournament.get_available_spots()

        args = ['some-tournament']
        opts = {'acceptplayer': player.id}
        call_command('waitinglist', *args, **opts)

        # Make sure player list increased by one
        self.assertEqual(
            self.tournament.get_player_list_count(),
            players_waiting_list_before + 1)

        # Make sure waiting list count reduced by one
        self.assertEqual(
            self.tournament.get_waiting_list_count(),
            players_waiting_list_before - 1)

        # Make sure available spots reduced by one
        self.assertEqual(
            self.tournament.get_available_spots(),
            spots_before - 1)

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




class PdgaTestCase(TestCase):
    @patch('tourney.tournament.utils.pdga.urlopen')
    def test_pdga(self, urlopen_mock):
        urlopen_mock.return_value = StringIO(pdga_response)

        rank = PDGARanking(123)

        # We know that Karl Johans ranking should be 1027
        # in our mocked response from PDGA
        self.assertEqual(rank.rating, 1027)

pdga_response = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML+RDFa 1.1//EN">
<html lang="en" dir="ltr" version="HTML+RDFa 1.1"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:dc="http://purl.org/dc/terms/"
  xmlns:foaf="http://xmlns.com/foaf/0.1/"
  xmlns:og="http://ogp.me/ns#"
  xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
  xmlns:sioc="http://rdfs.org/sioc/ns#"
  xmlns:sioct="http://rdfs.org/sioc/types#"
  xmlns:skos="http://www.w3.org/2004/02/skos/core#"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema#">
<head profile="http://www.w3.org/1999/xhtml/vocab">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, minimum-scale=1, user-scalable=no" />
<meta name="Generator" content="Drupal 7 (http://drupal.org)" />
<link rel="shortcut icon" href="http://www.pdga.com/sites/all/themes/pdga/favicon.ico" type="image/vnd.microsoft.icon" />
  <title>Jone    Eide #50956 | Professional Disc Golf Association</title>  
  <link type="text/css" rel="stylesheet" href="http://www.pdga.com/files/css/css_pbm0lsQQJ7A7WCCIMgxLho6mI_kBNgznNUWmTWcnfoE.css" media="all" />
<link type="text/css" rel="stylesheet" href="http://www.pdga.com/files/css/css_twsUmtGgd4KPiyXf3eCy-pJNJqHBm-KWgSwLdEsyhGk.css" media="all" />
<link type="text/css" rel="stylesheet" href="http://www.pdga.com/files/css/css_KpHsFsHL5G3x9EUJr5pMqQKsGs4fdCXEGrY6HhOgLHA.css" media="screen" />
<link type="text/css" rel="stylesheet" href="http://www.pdga.com/files/css/css_vlWeR1jayHYsF4bwVy6XOGHDD-9HxTQkR9NDLu5hHK8.css" media="all" />
<link type="text/css" rel="stylesheet" href="http://www.pdga.com/files/css/css_twoGX0mhaBBU5QnTPp91BKcz-Z8BXjS7sgTSjfdIfvc.css" media="all" />
<link type="text/css" rel="stylesheet" href="http://www.pdga.com/files/css/css_grhClt5P5zcB8oCgivElr3vCJfm1c86FZvugV2FxSi4.css" media="all" />

<!--[if (lt IE 9)&(!IEMobile)]>
<link type="text/css" rel="stylesheet" href="http://www.pdga.com/files/css/css_tqbOcWaj91wBE0-qFIjutB6piWPT71SZjJccs-NZjjk.css" media="all" />
<![endif]-->

<!--[if gte IE 9]><!-->
<link type="text/css" rel="stylesheet" href="http://www.pdga.com/files/css/css_yTtjahB6rTRl1UjrfWk1neYmLu0ZHJgLU_tlng1GOe0.css" media="all" />
<!--<![endif]-->
  <script type="text/javascript" src="http://www.pdga.com/files/js/js_0gj6QcpfRH2jzTbCQqf7kEkm4MXY0UA_sRhwPc8jC1o.js"></script>
<script type="text/javascript" src="http://www.pdga.com/files/js/js_1__UdgBELOPPsa1U3_nt8ttzzJ_5X3cfBGgpvnJMNXA.js"></script>
<script type="text/javascript">
<!--//--><![CDATA[//><!--
var _gaq = _gaq || [];_gaq.push(["_setAccount", "UA-6108714-1"]);_gaq.push(["_trackPageview"]);(function() {var ga = document.createElement("script");ga.type = "text/javascript";ga.async = true;ga.src = "http://www.pdga.com/files/googleanalytics/ga.js?n1m05c";var s = document.getElementsByTagName("script")[0];s.parentNode.insertBefore(ga, s);})();
//--><!]]>
</script>
<script type="text/javascript" src="http://www.pdga.com/files/js/js_ym7yBGpyoDQX0fTtvOxLMbqaotEHNddAfwWUJYRLVEw.js"></script>
<script type="text/javascript" src="http://www.pdga.com/files/js/js_43n5FBy8pZxQHxPXkf-sQF7ZiacVZke14b0VlvSA554.js"></script>
<script type="text/javascript">
<!--//--><![CDATA[//><!--
jQuery.extend(Drupal.settings, {"basePath":"\/","pathPrefix":"","ajaxPageState":{"theme":"pdga","theme_token":"ygYAIpzO0YS9QxrrBdhoXj1bf4Z9b1ou8c99Oa2bfmE","js":{"sites\/all\/modules\/contrib\/jquery_update\/replace\/jquery\/1.7\/jquery.min.js":1,"misc\/jquery.once.js":1,"misc\/drupal.js":1,"sites\/all\/libraries\/colorbox\/colorbox\/jquery.colorbox-min.js":1,"sites\/all\/modules\/contrib\/colorbox\/js\/colorbox.js":1,"sites\/all\/modules\/contrib\/colorbox\/styles\/default\/colorbox_default_style.js":1,"sites\/all\/modules\/contrib\/nice_menus\/superfish\/js\/superfish.js":1,"sites\/all\/modules\/contrib\/nice_menus\/superfish\/js\/jquery.bgiframe.min.js":1,"sites\/all\/modules\/contrib\/nice_menus\/superfish\/js\/jquery.hoverIntent.minified.js":1,"sites\/all\/modules\/contrib\/nice_menus\/nice_menus.js":1,"sites\/all\/modules\/contrib\/panels\/js\/panels.js":1,"sites\/all\/modules\/contrib\/views_slideshow\/js\/views_slideshow.js":1,"sites\/all\/modules\/contrib\/extlink\/extlink.js":1,"sites\/all\/libraries\/tablesorter\/jquery.tablesorter.js":1,"misc\/tableheader.js":1,"sites\/all\/modules\/custom\/tablesorter\/tablesorter.js":1,"sites\/all\/modules\/contrib\/google_analytics\/googleanalytics.js":1,"0":1,"sites\/all\/themes\/pdga\/js\/script.js":1,"sites\/all\/themes\/pdga\/js\/supposition.js":1,"sites\/all\/themes\/omega\/omega\/js\/jquery.formalize.js":1,"sites\/all\/themes\/omega\/omega\/js\/omega-mediaqueries.js":1},"css":{"modules\/system\/system.base.css":1,"modules\/system\/system.menus.css":1,"modules\/system\/system.messages.css":1,"modules\/system\/system.theme.css":1,"modules\/book\/book.css":1,"modules\/comment\/comment.css":1,"sites\/all\/modules\/contrib\/date\/date_api\/date.css":1,"sites\/all\/modules\/contrib\/date\/date_popup\/themes\/datepicker.1.7.css":1,"modules\/field\/theme\/field.css":1,"sites\/all\/modules\/contrib\/flexslider\/assets\/css\/flexslider_img.css":1,"modules\/node\/node.css":1,"modules\/user\/user.css":1,"sites\/all\/modules\/contrib\/views\/css\/views.css":1,"sites\/all\/modules\/contrib\/ckeditor\/ckeditor.css":1,"sites\/all\/modules\/contrib\/colorbox\/styles\/default\/colorbox_default_style.css":1,"sites\/all\/modules\/contrib\/ctools\/css\/ctools.css":1,"sites\/all\/modules\/contrib\/nice_menus\/nice_menus.css":1,"sites\/all\/modules\/contrib\/nice_menus\/nice_menus_default.css":1,"sites\/all\/modules\/contrib\/panels\/css\/panels.css":1,"sites\/all\/modules\/contrib\/views_slideshow\/views_slideshow.css":1,"sites\/all\/modules\/contrib\/extlink\/extlink.css":1,"sites\/all\/modules\/contrib\/panels\/plugins\/layouts\/onecol\/onecol.css":1,"sites\/all\/themes\/omega\/alpha\/css\/alpha-mobile.css":1,"sites\/all\/themes\/omega\/alpha\/css\/alpha-alpha.css":1,"sites\/all\/themes\/pdga\/css\/omega-visuals.css":1,"sites\/all\/themes\/pdga\/css\/normalize.css":1,"sites\/all\/themes\/omega\/omega\/css\/formalize.css":1,"sites\/all\/themes\/omega\/omega\/css\/omega-text.css":1,"sites\/all\/themes\/omega\/omega\/css\/omega-branding.css":1,"sites\/all\/themes\/omega\/omega\/css\/omega-menu.css":1,"sites\/all\/themes\/omega\/omega\/css\/omega-forms.css":1,"sites\/all\/themes\/pdga\/css\/global.css":1,"ie::normal::sites\/all\/themes\/pdga\/css\/pdga-alpha-default.css":1,"ie::normal::sites\/all\/themes\/pdga\/css\/pdga-alpha-default-normal.css":1,"ie::normal::sites\/all\/themes\/omega\/alpha\/css\/grid\/alpha_default\/normal\/alpha-default-normal-16.css":1,"ie::normal::sites\/all\/themes\/omega\/alpha\/css\/grid\/alpha_default\/normal\/alpha-default-normal-12.css":1,"narrow::sites\/all\/themes\/pdga\/css\/pdga-alpha-default.css":1,"narrow::sites\/all\/themes\/pdga\/css\/pdga-alpha-default-narrow.css":1,"sites\/all\/themes\/omega\/alpha\/css\/grid\/alpha_default\/narrow\/alpha-default-narrow-16.css":1,"sites\/all\/themes\/omega\/alpha\/css\/grid\/alpha_default\/narrow\/alpha-default-narrow-12.css":1,"normal::sites\/all\/themes\/pdga\/css\/pdga-alpha-default.css":1,"normal::sites\/all\/themes\/pdga\/css\/pdga-alpha-default-normal.css":1,"sites\/all\/themes\/omega\/alpha\/css\/grid\/alpha_default\/normal\/alpha-default-normal-16.css":1,"sites\/all\/themes\/omega\/alpha\/css\/grid\/alpha_default\/normal\/alpha-default-normal-12.css":1}},"colorbox":{"opacity":"0.85","current":"{current} of {total}","previous":"\u00ab Prev","next":"Next \u00bb","close":"Close","maxWidth":"100%","maxHeight":"100%","fixed":true,"__drupal_alter_by_ref":["default"]},"nice_menus_options":{"delay":"800","speed":"fast"},"extlink":{"extTarget":"_blank","extClass":"ext","extSubdomains":1,"extExclude":"","extInclude":"","extAlert":0,"extAlertText":"This link will take you to an external web site. We are not responsible for their content.","mailtoClass":"mailto"},"tablesorter":{"selectors":["#player-results-mpo"]},"googleanalytics":{"trackOutbound":1,"trackMailto":1,"trackDownload":1,"trackDownloadExtensions":"7z|aac|arc|arj|asf|asx|avi|bin|csv|doc|exe|flv|gif|gz|gzip|hqx|jar|jpe?g|js|mp(2|3|4|e?g)|mov(ie)?|msi|msp|pdf|phps|png|ppt|qtm?|ra(m|r)?|sea|sit|tar|tgz|torrent|txt|wav|wma|wmv|wpd|xls|xml|z|zip"},"omega":{"layouts":{"primary":"normal","order":["narrow","normal"],"queries":{"narrow":"all and (min-width: 740px) and (min-device-width: 740px), (max-device-width: 800px) and (min-width: 740px) and (orientation:landscape)","normal":"all and (min-width: 980px) and (min-device-width: 980px), all and (max-device-width: 1024px) and (min-width: 1024px) and (orientation:landscape)"}}}});
//--><!]]>
</script>
  <!--[if lt IE 9]><script src="http://html5shiv.googlecode.com/svn/trunk/html5.js"></script><![endif]-->
</head>
<body class="html not-front not-logged-in page-player page-player- page-player-50956 panel-custom-title context-player">
  <div id="skip-link">
    <a href="#main-content" class="element-invisible element-focusable">Skip to main content</a>
  </div>
  <div class="region region-page-top" id="region-page-top">
  <div class="region-inner region-page-top-inner">
      </div>
</div>  <div class="page clearfix" id="page">
      <header id="section-header" class="section section-header">
  <div id="zone-branding-wrapper" class="zone-wrapper zone-branding-wrapper clearfix">  
  <div id="zone-branding" class="zone zone-branding clearfix container-16">
    <div class="grid-11 region region-branding" id="region-branding">
  <div class="region-inner region-branding-inner">
        <div class="branding-data clearfix">
            <div class="logo-img">
        <a href="/" rel="home" title=""><img src="http://www.pdga.com/sites/all/themes/pdga/logo.png" alt="" id="logo" /></a>      </div>
                </div>
          </div>
</div><div class="grid-5 region region-user-bar" id="region-user-bar">
  <div class="region-inner region-user-bar-inner">
    <div class="block block-panels-mini block-header-user-bar block-panels-mini-header-user-bar odd block-without-title" id="block-panels-mini-header-user-bar">
  <div class="block-inner clearfix">
                
    <div class="content clearfix">
      <div class="panel-display panel-1col clearfix" id="mini-panel-header_user_bar">
  <div class="panel-panel panel-col">
    <div><div class="panel-pane pane-custom pane-1 pane-social-links inline clearfix" >
  
      
  
  <div class="pane-content">
    <ul class="menu social-links"><li><a target="_blank" class="rss" href="/frontpage/feed" title="Subscribe to the PDGA RSS Feed">RSS Feed</a></li>
<li><a target="_blank" class="twitter" href="http://twitter.com/pdga" title="PDGA on Twitter">Twitter</a></li>
<li><a target="_blank" class="facebook" href="http://www.facebook.com/pdga" title="PDGA on Facebook">Facebook</a></li>
<li><a target="_blank" class="flickr" href="http://www.flickr.com/photos/pdga/collections/" title="PDGA on Flickr">Flickr</a></li>
<li><a target="_blank" class="youtube" href="http://www.youtube.com/pdgamedia" title="PDGA on YouTube">YouTube</a></li>
</ul>  </div>

  
  </div>
<div class="panel-separator"></div><div class="panel-pane pane-pdga-search-searchapi-block pane-search-form" >
  
        <h2 class="pane-title">Search</h2>
    
  
  <div class="pane-content">
    
<div class="container-inline">
  <form class="search-form" action="/search" method="get" id="search-form" accept-charset="UTF-8">
    <div>
      <div class="form-item form-type-textfield form-item-keywords">
        <input type="text" name="keywords" value="" size="15" maxlength="128" class="form-text">
      </div>
    </div>
    <div class="form-actions">
      <input type="submit" value="Search" class="form-submit">
    </div>
  </form>
</div>
  </div>

  
  </div>
<div class="panel-separator"></div><div class="panel-pane pane-block pane-system-user-menu inline" >
  
      
  
  <div class="pane-content">
    <ul class="menu"><li class="first leaf"><a href="/user/login?destination=player/50956" title="">Login</a></li>
<li class="leaf"><a href="/join-pdga-today" title="">Join &amp; Renew</a></li>
<li class="last leaf"><a href="/contact" title="">Contact</a></li>
</ul>  </div>

  
  </div>
</div>
  </div>
</div>
    </div>
  </div>
</div>  </div>
</div>  </div>
</div><div id="zone-menu-wrapper" class="zone-wrapper zone-menu-wrapper clearfix">  
  <div id="zone-menu" class="zone zone-menu clearfix container-12">
    <div class="grid-12 region region-menu" id="region-menu">
  <div class="region-inner region-menu-inner">
        <section class="block block-nice-menus block-1 block-nice-menus-1 odd" id="block-nice-menus-1">
  <div class="block-inner clearfix">
              <h2 class="block-title">Main Menu</h2>
            
    <div class="content clearfix">
      <ul class="nice-menu nice-menu-down" id="nice-menu-1"><li class="menu-5628 menu-path-front  first   odd  "><a href="/">Home</a></li>
<li class="menu-5629 menuparent  menu-path-nolink   even  "><div title="" class="nolink">About</div><ul><li class="menu-5637 menu-path-node-21340  first   odd  "><a href="/introduction">What is Disc Golf?</a></li>
<li class="menu-7824 menu-path-node-200525   even  "><a href="/news">News Archive</a></li>
<li class="menu-5638 menu-path-node-21339   odd  "><a href="/history">History</a></li>
<li class="menu-5639 menu-path-faq   even   last "><a href="/faq">FAQs</a></li>
</ul></li>
<li class="menu-5630 menuparent  menu-path-nolink   odd  "><div title="" class="nolink">Membership</div><ul><li class="menu-5640 menu-path-node-21322  first   odd  "><a href="/join-pdga-today">Join &amp; Renew</a></li>
<li class="menu-5641 menu-path-players   even  "><a href="/players">Player Search</a></li>
<li class="menu-5642 menu-path-players-stats   odd  "><a href="/players/stats">Player Statistics</a></li>
<li class="menu-5643 menuparent  menu-path-node-21404   even  "><a href="/players/rankings">Player Rankings</a><ul><li class="menu-5669 menu-path-node-21313  first   odd  "><a href="/pdga-world-rankings">World Rankings</a></li>
<li class="menu-5670 menu-path-node-21382   even   last "><a href="/pdga-continental-rankings">Continental Rankings</a></li>
</ul></li>
<li class="menu-5676 menu-path-node-28442   odd  "><a href="/pdga-player-classifications-divisions">Player Classifications &amp; Divisions</a></li>
<li class="menu-5677 menu-path-node-21365   even  "><a href="/pdga-player-rookie-year">Player &amp; Rookie of the Year</a></li>
<li class="menu-5646 menu-path-node-21372   odd  "><a href="/seniors">Seniors</a></li>
<li class="menu-5644 menuparent  menu-path-node-21364   even   last "><a href="/women">Women</a><ul><li class="menu-9149 menu-path-node-21398  first   odd   last "><a href="/women/global-event">Women&#039;s Global Event</a></li>
</ul></li>
</ul></li>
<li class="menu-5631 menuparent  menu-path-nolink   even  "><div title="" class="nolink">Events</div><ul><li class="menu-5647 menu-path-tour-events  first   odd  "><a href="/tour/events">Event Schedule &amp; Results</a></li>
<li class="menu-5648 menu-path-tour-search   even  "><a href="/tour/search">Event Search</a></li>
<li class="menu-7045 menu-path-node-21343   odd  "><a href="/national-tour">National Tour</a></li>
<li class="menu-5649 menuparent  menu-path-node-21370   even  "><a href="/major-disc-golf-events">Major Disc Golf Events</a><ul><li class="menu-7851 menu-path-node-200112  first   odd   last "><a href="/2014usmasters">2014 US Masters</a></li>
</ul></li>
<li class="menu-5650 menuparent  menu-path-node-21355   odd  "><a href="/world-championships">World Championships</a><ul><li class="menu-7850 menu-path-node-200552  first   odd   last "><a href="/2014proworlds">2014 Pro Worlds</a></li>
</ul></li>
<li class="menu-5651 menuparent  menu-path-node-21391   even  "><a href="/leagues">PDGA Leagues</a><ul><li class="menu-9165 menu-path-leagues-events  first   odd   last "><a href="/leagues/events" title="">League Schedule</a></li>
</ul></li>
<li class="menu-5652 menuparent  menu-path-node-21342   odd   last "><a href="/td">Tournament Directors</a><ul><li class="menu-7811 menu-path-node-28432  first   odd  "><a href="/pdga-event-sanctioning-agreement">Event Sanctioning</a></li>
<li class="menu-7812 menu-path-node-30232   even   last "><a href="/event-payments">Event Payments</a></li>
</ul></li>
</ul></li>
<li class="menu-5632 menuparent  menu-path-nolink   odd  "><div title="" class="nolink">Courses</div><ul><li class="menu-7059 menu-path-course-directory-advanced  first   odd  "><a href="/course-directory/advanced" title="">Course Search</a></li>
<li class="menu-5655 menu-path-course-directory   even  "><a href="/course-directory">Course Directory Map</a></li>
<li class="menu-5656 menu-path-node-21324   odd   last "><a href="/course-development">Course Development</a></li>
</ul></li>
<li class="menu-5668 menuparent  menu-path-nolink   even  "><div title="" class="nolink">Rules</div><ul><li class="menu-9157 menu-path-node-8371  first   odd  "><a href="/rules" title="">Overview</a></li>
<li class="menu-5657 menu-path-node-24567   even  "><a href="/rules/official-rules-disc-golf">Official Rules of Disc Golf</a></li>
<li class="menu-6102 menu-path-node-8397   odd  "><a href="/rules/competition-manual-disc-golf-events">Competition Manual for Disc Golf Events</a></li>
<li class="menu-6103 menu-path-node-23201   even  "><a href="/documents/divisions-ratings-points-factors">Divisions, Ratings and Points Factors</a></li>
<li class="menu-5721 menu-path-node-21335   odd  "><a href="/rules/technical-standards">Technical Standards</a></li>
<li class="menu-5658 menu-path-node-21312   even   last "><a href="/rules/becoming-a-pdga-official">Certified Official&#039;s Exam</a></li>
</ul></li>
<li class="menu-5634 menuparent  menu-path-nolink   odd  "><div title="" class="nolink">Media</div><ul><li class="menu-5659 menu-path-node-21353  first   odd  "><a href="/discgolfer-magazine">DiscGolfer Magazine</a></li>
<li class="menu-5661 menu-path-videos   even  "><a href="/videos">Videos</a></li>
<li class="menu-5660 menu-path-flickrcom-photos-pdga   odd  "><a href="http://www.flickr.com/photos/pdga">Flickr</a></li>
<li class="menu-5662 menu-path-facebookcom-pdga   even  "><a href="http://www.facebook.com/pdga">Facebook</a></li>
<li class="menu-5663 menu-path-twittercom-pdga   odd   last "><a href="http://twitter.com/pdga">Twitter</a></li>
</ul></li>
<li class="menu-5635 menu-path-node-21338   even  "><a href="/international">International</a></li>
<li class="menu-5636 menuparent  menu-path-nolink   odd   last "><div title="" class="nolink">More</div><ul><li class="menu-5664 menu-path-node-21368  first   odd  "><a href="/advertising">Advertising</a></li>
<li class="menu-5715 menu-path-node-21325   even  "><a href="/affiliate_club">Affiliate Club Program</a></li>
<li class="menu-5714 menu-path-node-30231   odd  "><a href="/board-of-directors">Board of Directors</a></li>
<li class="menu-5716 menu-path-contact   even  "><a href="/contact" title="">Contact</a></li>
<li class="menu-5717 menu-path-node-21352   odd  "><a href="/pdga-and-disc-golf-demographics">Demographics</a></li>
<li class="menu-5718 menu-path-node-21354   even  "><a href="/pdga-disciplinary-process">Disciplinary Process</a></li>
<li class="menu-7849 menu-path-discussionpdgacom   odd  "><a href="http://discussion.pdga.com" title="">Discussion Board</a></li>
<li class="menu-5666 menu-path-node-21357   even  "><a href="/elections">Elections</a></li>
<li class="menu-5665 menu-path-node-30227   odd  "><a href="/IDGC">International Disc Golf Center</a></li>
<li class="menu-5719 menu-path-node-21344   even  "><a href="/pdga-organization-documents">Organization Documents</a></li>
<li class="menu-5720 menu-path-node-28438   odd  "><a href="/points">Points</a></li>
<li class="menu-7799 menu-path-pdgastorecom   even  "><a href="http://www.pdgastore.com" title="">Pro Shop</a></li>
<li class="menu-5667 menu-path-node-21356   odd  "><a href="/pdga-player-course-rating-system">Ratings</a></li>
<li class="menu-7795 menu-path-taxonomy-term-743   even   last "><a href="/pdga-documents" title="">Recently Updated Documents</a></li>
</ul></li>
</ul>
    </div>
  </div>
</section>  </div>
</div>
  </div>
</div><div id="zone-header-wrapper" class="zone-wrapper zone-header-wrapper clearfix">  
  <div id="zone-header" class="zone zone-header clearfix container-12">
    <div class="grid-12 region region-header top-banner" id="region-header">
  <div class="region-inner region-header-inner">
    <div class="block block-block block-7 block-block-7 odd block-without-title" id="block-block-7">
  <div class="block-inner clearfix">
                
    <div class="content clearfix">
      <script type="text/javascript">
<!--//--><![CDATA[// ><!--
<!--//<![CDATA[
   var m3_u = (location.protocol=='https:'?'https://ads.pdga.com/openx/www/delivery/ajs.php':'http://ads.pdga.com/openx/www/delivery/ajs.php');
   var m3_r = Math.floor(Math.random()*99999999999);
   if (!document.MAX_used) document.MAX_used = ',';
   document.write ("<scr"+"ipt type='text/javascript' src='"+m3_u);
   document.write ("?zoneid=31");
   document.write ('&amp;cb=' + m3_r);
   if (document.MAX_used != ',') document.write ("&amp;exclude=" + document.MAX_used);
   document.write (document.charset ? '&amp;charset='+document.charset : (document.characterSet ? '&amp;charset='+document.characterSet : ''));
   document.write ("&amp;loc=" + escape(window.location));
   if (document.referrer) document.write ("&amp;referer=" + escape(document.referrer));
   if (document.context) document.write ("&context=" + escape(document.context));
   if (document.mmm_fo) document.write ("&amp;mmm_fo=1");
   document.write ("'><\/scr"+"ipt>");
//]]]]><![CDATA[>-->
//--><!]]>
</script>    </div>
  </div>
</div>  </div>
</div>  </div>
</div></header>    
      <section id="section-content" class="section section-content">
  <div id="zone-content-wrapper" class="zone-wrapper zone-content-wrapper clearfix">  
  <div id="zone-content" class="zone zone-content clearfix container-16">    
        
        <div class="grid-16 region region-content" id="region-content">
  <div class="region-inner region-content-inner">
    <a id="main-content"></a>
                <h1 class="title" id="page-title">Jone   Eide #50956</h1>
                        <div class="block block-system block-main block-system-main odd block-without-title" id="block-system-main">
  <div class="block-inner clearfix">
                
    <div class="content clearfix">
      <div class="panel-display omega-grid pdga-one-col clearfix" >

  <div class="panel-panel grid-16">
    <div class="inside"><div class="panel-pane pane-page-title" >
  
      
  
  <div class="pane-content">
    <h1>Jone     Eide #50956</h1>
  </div>

  
  </div>
<div class="panel-separator"></div><div class="panel-pane pane-horizontal-rule" >
  
      
  
  <div class="pane-content">
    <hr />  </div>

  
  </div>
<div class="panel-separator"></div><div class="panel-pane pane-player-player-info" >
  
        <h2 class="pane-title">Player Info</h2>
    
  
  <div class="pane-content">
    <ul class="player-info info-list"><li class="location"><strong>Location:</strong> Haugesund, Norway</li><li class="classification"><strong>Classification: </strong> Professional</li><li class="membership-status"><strong>Membership Status: </strong> Current <small class="membership-expiration-date">(until 31-Dec-2016)</small></li><li class="current-rating"><strong>Current Rating:</strong> 932 <small class="rating-date">(as of 18-Feb-2014)</small></li></ul>  </div>

  
  </div>
<div class="panel-separator"></div><div class="panel-pane pane-player-player-stats" >
  
        <h2 class="pane-title">Player Statistics</h2>
    
  
  <div class="pane-content">
    <div class="item-list"><ul class="tabs primary"><li class="first"><a href="/player/50956" class="active">Player Statistics</a></li><li><a href="/player/50956/details">Ratings Detail</a></li><li class="last"><a href="/player/50956/history">Ratings History</a></li></ul></div><div class="year-link"><div class="item-list"><ul class="tabs secondary"><li class="first"><a href="/player/50956" class="active active">2013</a></li><li class="last"><a href="/player/50956/stats/2012">2012</a></li></ul></div></div><h3>2013 Season Totals</h3><table class="sticky-enabled">
 <thead><tr><th>Classification</th><th class="tournament-count">Tournaments Played</th><th class="points">Points</th><th class="prize">Prize</th> </tr></thead>
<tbody>
 <tr class="odd"><td>Professional</td><td class="tournament-count">5</td><td class="points">960</td><td class="prize">$112.63</td> </tr>
</tbody>
</table>
<h3>Tournament Results</h3><h4>Open</h4><table id="player-results-mpo" class="sticky-enabled">
 <thead><tr><th class="place">Place</th><th class="points">Points</th><th class="tournament">Tournament</th><th class="dates">Dates</th><th class="total">Total</th><th class="prize">Prize</th> </tr></thead>
<tbody>
 <tr class="odd"><td class="place">24</td><td class="points">173</td><td class="tournament"><a href="/tour/event/15384">Bergen Open</a></td><td class="dates">20-Apr to 21-Apr-2013</td><td class="total">190</td><td class="prize"></td> </tr>
 <tr class="even"><td class="place">9</td><td class="points">353</td><td class="tournament"><a href="/tour/event/15385">Stovnerputten 2013</a></td><td class="dates">22-Jun-2013</td><td class="total">174</td><td class="prize">$112</td> </tr>
 <tr class="odd"><td class="place">37</td><td class="points">215</td><td class="tournament"><a href="/tour/event/16028">Norwegian Championship</a></td><td class="dates">02-Aug-2013</td><td class="total">261</td><td class="prize"></td> </tr>
 <tr class="even"><td class="place">27</td><td class="points">150</td><td class="tournament"><a href="/tour/event/15963">Skien Open</a></td><td class="dates">16-Aug to 18-Aug-2013</td><td class="total">262</td><td class="prize"></td> </tr>
 <tr class="odd"><td class="place">5</td><td class="points">70</td><td class="tournament"><a href="/tour/event/15961">Haugaland Open</a></td><td class="dates">07-Sep-2013</td><td class="total">128</td><td class="prize"></td> </tr>
</tbody>
</table>
  </div>

  
  </div>
</div>
  </div>

</div>
    </div>
  </div>
</div>      </div>
</div>  </div>
</div></section>    
  
      <footer id="section-footer" class="section section-footer">
  <div id="zone-footer-wrapper" class="zone-wrapper zone-footer-wrapper clearfix">  
  <div id="zone-footer" class="zone zone-footer clearfix container-12">
    <div class="grid-12 region region-footer-first" id="region-footer-first">
  <div class="region-inner region-footer-first-inner">
    <div class="block block-panels-mini block-footer-menu block-panels-mini-footer-menu odd block-without-title" id="block-panels-mini-footer-menu">
  <div class="block-inner clearfix">
                
    <div class="content clearfix">
      <div class="panel-display panel-1col clearfix" id="mini-panel-footer_menu">
  <div class="panel-panel panel-col">
    <div><div class="panel-pane pane-block pane-menu-menu-footer clearfix" >
  
      
  
  <div class="pane-content">
    <ul class="menu"><li class="first expanded"><div class="nolink">Disc Golf</div><ul class="menu"><li class="first leaf"><a href="/introduction" title="">What is Disc Golf</a></li>
<li class="leaf"><a href="/rules">Official Rules of Disc Golf</a></li>
<li class="last leaf"><a href="/course-directory">Course Directory</a></li>
</ul></li>
<li class="expanded"><div class="nolink">Membership</div><ul class="menu"><li class="first leaf"><a href="/membership" title="">Join &amp; Renew</a></li>
<li class="leaf"><a href="/members/benefits">Benefits</a></li>
<li class="last leaf"><a href="/players" title="">Member Search</a></li>
</ul></li>
<li class="expanded"><div class="nolink">Tour</div><ul class="menu"><li class="first leaf"><a href="/tour/events" title="">Schedule &amp; Results</a></li>
<li class="leaf"><a href="/national-tour" title="">National Tour</a></li>
<li class="leaf"><a href="/major-disc-golf-events" title="">PDGA Major Events</a></li>
<li class="leaf"><a href="/world-championships">World Championships</a></li>
<li class="last leaf"><a href="/td" title="">Tournament Directors</a></li>
</ul></li>
<li class="expanded"><div class="nolink">Media</div><ul class="menu"><li class="first leaf"><a href="/discgolfer-magazine" title="">DiscGolfer Magazine</a></li>
<li class="leaf"><a href="http://www.flickr.com/photos/pdga" title="">Photos</a></li>
<li class="leaf"><a href="/videos" title="">Videos</a></li>
<li class="leaf"><a href="https://twitter.com/pdga" title="">Twitter</a></li>
<li class="last leaf"><a href="https://www.facebook.com/pdga" title="">Facebook</a></li>
</ul></li>
<li class="last expanded"><div class="nolink">More</div><ul class="menu"><li class="first leaf"><a href="/contact" title="">Contact</a></li>
<li class="leaf"><a href="/international">International</a></li>
<li class="leaf"><a href="http://www.pdgastore.com" title="">Pro Shop</a></li>
<li class="last leaf"><a href="/tos">Terms of Use</a></li>
</ul></li>
</ul>  </div>

  
  </div>
</div>
  </div>
</div>
    </div>
  </div>
</div>  </div>
</div><div class="grid-12 region region-footer-second" id="region-footer-second">
  <div class="region-inner region-footer-second-inner">
    <div class="block block-panels-mini block-footer-secondary block-panels-mini-footer-secondary odd block-without-title" id="block-panels-mini-footer-secondary">
  <div class="block-inner clearfix">
                
    <div class="content clearfix">
      <div class="panel-display panel-1col clearfix" id="mini-panel-footer_secondary">
  <div class="panel-panel panel-col">
    <div><div class="panel-pane pane-pdga-architecture-footer" >
  
      
  
  <div class="pane-content">
    <p>Copyright © 1998-2014. Professional Disc Golf Association. All Rights Reserved.</p>
<p>IDGC - Wildwood Park, 3828 Dogwood Lane, Appling, GA 30802-3012 PH: 706-261-6342</p>
  </div>

  
  </div>
</div>
  </div>
</div>
    </div>
  </div>
</div>  </div>
</div>  </div>
</div></footer>  </div>  </body>
</html>

"""
