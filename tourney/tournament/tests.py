#-*-coding: utf8
from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.utils.timezone import utc
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.timezone import now

from datetime import datetime, date, timedelta

from nose.plugins.attrib import attr

from .forms import RegistrationForm
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

    return Player.objects.create(
        **player_kwargs)


def generate_user():
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


class WaitingListTest(TournamentTestCase):
    def setUp(self, *kargs, **kwargs):

        super(WaitingListTest, self).setUp(
            *kargs, **kwargs)

        self.tournament.max_players = 1
        self.tournament.wildcard_spots = 0

        generate_tournament_player(self.tournament)
        generate_tournament_player(self.tournament)



class WaitingListEmailTest(WaitingListTest):
    def setUp(self, *kargs, **kwargs):

        super(WaitingListEmailTest, self).setUp(
            *kargs, **kwargs)

        self.tournament.tournament_admin_email = 'foo@bar.com'
        player = self.tournament.tournamentplayer_set.get(
            is_waiting_list=True)

        player.player.email = 'bar@foo.com'
        self.player = player

    def email_test(self):
        outbox_length_before = len(mail.outbox)
        self.player.send_registration_email()
        self.assertEqual(
            len(mail.outbox),
            outbox_length_before + 1)


class WaitingListCommandTest(WaitingListTest):
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


from tourney.tournament.utils.pdga import PDGARanking
from mock import patch
from StringIO import StringIO



class PdgaTestCase(TestCase):
    @patch('tourney.tournament.utils.pdga.urlopen')
    def test_pdga(self, urlopen_mock):
        urlopen_mock.return_value = StringIO(pdga_response)

        rank = PDGARanking(123)

        # We know that Karl Johans ranking should be 1027
        # in our mocked response from PDGA
        self.assertEqual(rank.rating, 1027)



pdga_response = """<!DOCTYPE html>
<html lang="en-US">

<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <title>Karl Johan Hoj Nybo #28903 | Professional Disc Golf Association</title>
  <meta name="keywords" content="PDGA,Professional Disc Golf Association,disc golf,frisbee golf,frolf,courses,tournaments,schedule,results,membership" />
<meta name="robots" content="index,follow" />
<link rel="shortcut icon" href="/sites/all/themes/platform/favicon.ico?s=18f3acbca4490cbf2eae40637cd5b9f0" type="image/x-icon" />
  <style type="text/css" media="all">@import "/files/css/712a9ded37f0698597879b8e409498af.css";</style>
  <script type="text/javascript" src="/files/js/4a08e96aeeaafdd051fa38fe334f8034.js?s=18f3acbca4490cbf2eae40637cd5b9f0"></script>
<script type="text/javascript">Drupal.extend({ settings: { "fivestar": { "titleUser": "Your rating: ", "titleAverage": "Average: ", "feedbackSavingVote": "Saving your vote...", "feedbackVoteSaved": "Your vote has been saved.", "feedbackDeletingVote": "Deleting your vote...", "feedbackVoteDeleted": "Your vote has been deleted." }, "extlink": { "extTarget": "_blank", "extClass": 0, "extSubdomains": 1, "extExclude": "", "extInclude": "", "extAlert": 0, "extAlertText": "This link will take you to an external web site. We are not responsible for their content.", "mailtoClass": 0 }, "googleanalytics": { "trackOutgoing": 1, "trackMailto": 1, "trackDownload": 1, "trackDownloadExtensions": "7z|aac|avi|csv|doc|exe|flv|gif|gz|jpe?g|js|mp(3|4|e?g)|mov|pdf|phps|png|ppt|rar|sit|tar|torrent|txt|wma|wmv|xls|xml|zip", "LegacyVersion": 0 } } });</script>
<script type="text/javascript">$("document").ready( function() { $(".results").tablesorter();})</script>  <!-- begin script to create random number for ads -->
  <script type="text/javascript">
  <!--
  sgi_ord=Math.random()*10000000000000000;
  sgi_tile=1;
  //-->
  </script>
  <!-- End random number script -->
</head>

<body class="not-front not-logged-in sidebar-right">

<!-- wrapper -->

<div id="wrapper">

	<div id="above-content">
		<div class="adblock-728x90 top-adspace"><div class="block block-block " id="block-block-40">
  <div class="block-inner">

    
    <div class="block-content">
      <script type='text/javascript'><!--//<![CDATA[
   var m3_u = (location.protocol=='https:'?'https://www.pdga.com/openx/www/delivery/ajs.php':'http://www.pdga.com/openx/www/delivery/ajs.php');
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
//]]>--></script>    </div>
    
  </div>
</div>
 </div>	    <div id="rightOf-728"><div class="block block-search " id="block-search-0">
  <div class="block-inner">

    <p class="block-title"> Search </p>
    <div class="block-content">
      <form action="/player_stats/44378/2012?s=18f3acbca4490cbf2eae40637cd5b9f0"  accept-charset="UTF-8" method="post" id="search-block-form">
<div><div class="container-inline"><div class="form-item" id="edit-search-block-form-keys-wrapper">
 <input type="text" maxlength="128" name="search_block_form_keys" id="edit-search-block-form-keys"  size="15" value="" title="Enter the terms you wish to search for." class="form-text" />
</div>
<input type="submit" name="op" id="edit-submit" value="Search"  class="form-submit" />
<input type="hidden" name="form_id" id="edit-search-block-form" value="search_block_form"  />
</div>
</div></form>
    </div>
    
  </div>
</div>
<div class="block block-menu block-&lt;none&gt; " id="block-menu-369">
  <div class="block-inner">

    
    <div class="block-content">
      
<ul class="menu">
<li class="leaf"><a href="/user?s=18f3acbca4490cbf2eae40637cd5b9f0">Login</a></li>
<li class="leaf"><a href="/contact?s=18f3acbca4490cbf2eae40637cd5b9f0">Contact</a></li>

</ul>
    </div>
    
  </div>
</div>
 </div>	    <div class="clear"></div>
	</div>

    <!-- top -->
    <div id="top">

        
        <div id="header">

			            <h1 class="logo">
                <a href="/?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Home">
                <img src="/files/platform_logo.jpg" alt="Professional Disc Golf Association" align="middle" />
                </a>
            </h1>
            

            <div id="header_graphic">
			<div class="block block-headerimage " id="block-headerimage-1">
  <div class="block-inner">

    
    <div class="block-content">
      <div class="field field-type-image field-field-header-image"><div class="field-items"><div class="field-item odd"><img src="http://www.pdga.com/files/headers/header_chains.jpg" alt="header_chains.jpg" title="header_chains.jpg" width="630" height="110" class="imagefield imagefield-field_header_image" /></div></div></div>    </div>
    
  </div>
</div>
			</div>
        </div>

    </div>
    <!-- /top -->

    <!-- nav -->
    <div id="nav">
    	<div class="block block-nice_menus block-&lt;none&gt; " id="block-nice_menus-1">
  <div class="block-inner">

    
    <div class="block-content">
      <ul class="nice-menu nice-menu-down" id="nice-menu-1"><li id="menu-93" class="menu-path-www.pdga.com"><a href="http://www.pdga.com">Home</a></li>
<li id="menu-334" class="menuparent menu-path-none"><a title="About">About</a><ul><li id="menu-397" class="menu-path-node-232"><a href="/introduction?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Introduction to Disc Golf">What is Disc Golf</a></li>
<li id="menu-508" class="menu-path-node-228"><a href="/history?s=18f3acbca4490cbf2eae40637cd5b9f0" title="History of disc golf">History</a></li>
<li id="menu-279" class="menu-path-faq"><a href="/faq?s=18f3acbca4490cbf2eae40637cd5b9f0">FAQ</a></li>
</ul>
</li>
<li id="menu-276" class="menuparent menu-path-none"><a title="Membership">Membership</a><ul><li id="menu-479" class="menu-path-node-178"><a href="/join?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information on joining the PDGA">Join &amp; Renew</a></li>
<li id="menu-481" class="menu-path-member_search"><a href="/members?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Player Search">Player Search</a></li>
<li id="menu-476" class="menu-path-player_stats_ratings_search"><a href="/player_stats_ratings_search?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Player Statistics">Player Statistics</a></li>
<li id="menu-602" class="menu-path-node-464"><a href="/player-ratings-search?s=18f3acbca4490cbf2eae40637cd5b9f0">Player Ratings</a></li>
<li id="menu-403" class="menu-path-node-152"><a href="/world-rankings?s=18f3acbca4490cbf2eae40637cd5b9f0" title="World Rankings">Player Rankings</a></li>
<li id="menu-499" class="menu-path-node-4899"><a href="/player-rookie-of-the-year-awards?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information and current standings on the Player and Rooke of the Year contest.">Player &amp; Rookie of the Year</a></li>
<li id="menu-529" class="menu-path-node-5612"><a href="/seniors?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Info page dedicated to senior disc golfers ">Seniors</a></li>
<li id="menu-514" class="menu-path-node-4806"><a href="/women?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Info page dedicated to women disc golfers">Women</a></li>
</ul>
</li>
<li id="menu-277" class="menuparent menu-path-none"><a title="PDGA Tour">PDGA Tour</a><ul><li id="menu-475" class="menu-path-tour_schedule"><a href="/tour_schedule?s=18f3acbca4490cbf2eae40637cd5b9f0" title="List of PDGA sanctioned events and results">Event Schedule &amp; Results</a></li>
<li id="menu-430" class="menu-path-node-354"><a href="/national-tour?s=18f3acbca4490cbf2eae40637cd5b9f0" title="PDGA National Tour and Drive for the Championship Standings">National Tour</a></li>
<li id="menu-523" class="menu-path-node-5210"><a href="/pdga-major-events?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information on PDGA Major Events">Major Disc Golf Events</a></li>
<li id="menu-478" class="menu-path-node-727"><a href="/world-championships?s=18f3acbca4490cbf2eae40637cd5b9f0" title="World Championships Info Page">World Championships</a></li>
<li id="menu-588" class="menu-path-node-83431"><a href="/leagues?s=18f3acbca4490cbf2eae40637cd5b9f0">PDGA Leagues</a></li>
<li id="menu-477" class="menu-path-node-326"><a href="/tdinfo?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Resources for Tournament Directors">Tournament Directors</a></li>
</ul>
</li>
<li id="menu-278" class="menuparent menu-path-none"><a title="Courses">Courses</a><ul><li id="menu-404" class="menu-path-node-1429"><a href="/course_directory?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Course Directory">Course Directory</a></li>
<li id="menu-367" class="menu-path-node-187"><a href="/course-development?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Resources for developing a new course">Course Development</a></li>
</ul>
</li>
<li id="menu-509" class="menuparent menu-path-none"><a title="Rules">Rules</a><ul><li id="menu-603" class="menu-path-node-100021"><a href="/rules?s=18f3acbca4490cbf2eae40637cd5b9f0">Official Rules and Regulations of Disc Golf</a></li>
<li id="menu-474" class="menu-path-certified_officials"><a href="/certified_officials?s=18f3acbca4490cbf2eae40637cd5b9f0" title="List of certified officials">Certified Officials</a></li>
<li id="menu-555" class="menu-path-www.pdgastore.com-store-officials-exam.html"><a href="http://www.pdgastore.com/store/officials-exam.html" title="Take the Certified Official&#039;s Exam">Official&#039;s Exam</a></li>
</ul>
</li>
<li id="menu-280" class="menuparent menu-path-none"><a title="Media">Media</a><ul><li id="menu-507" class="menu-path-node-722"><a href="/discgolfer-magazine?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information about the official publication of the PDGA">DiscGolfer Magazine</a></li>
<li id="menu-411" class="menu-path-www.flickr.com-photos-pdga"><a href="http://www.flickr.com/photos/pdga" title="PDGA Media Photos">Photos</a></li>
<li id="menu-405" class="menu-path-videos"><a href="/videos?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Videos">Videos</a></li>
<li id="menu-655" class="menu-path-www.facebook.com-pdga"><a href="http://www.facebook.com/pdga">Facebook</a></li>
<li id="menu-656" class="menu-path-twitter.com-pdga"><a href="http://twitter.com/pdga">Twitter</a></li>
</ul>
</li>
<li id="menu-422" class="menuparent menu-path-none"><a title="Pro Shop">Pro Shop</a><ul><li id="menu-559" class="menu-path-www.pdgastore.com"><a href="http://www.pdgastore.com" title="Shop at the PDGA online store">PDGA Store</a></li>
<li id="menu-560" class="menu-path-www.pdgamerchandise.com"><a href="http://www.pdgamerchandise.com" title="Shop for customized PDGA merchandise">PDGA Merchandise</a></li>
</ul>
</li>
<li id="menu-494" class="menu-path-node-224"><a href="/international?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information on the PDGA International Program">International</a></li>
<li id="menu-282" class="menu-path-www.pdga.com-discussion"><a href="http://www.pdga.com/discussion?s=18f3acbca4490cbf2eae40637cd5b9f0">Discussion</a></li>
<li id="menu-281" class="menuparent menu-path-none"><a title="More">More</a><ul><li id="menu-513" class="menu-path-node-5138"><a href="/advertising?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information about advertising with the PDGA">Advertising</a></li>
<li id="menu-488" class="menu-path-node-191"><a href="/affiliate_club?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information on the PDGA Affilicate Club">Affiliate Club Program</a></li>
<li id="menu-489" class="menu-path-contact"><a href="/contact?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Contact the PDGA">Contact</a></li>
<li id="menu-490" class="menu-path-node-702"><a href="/demographics?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Demographics">Demographics</a></li>
<li id="menu-491" class="menu-path-node-724"><a href="/discipline?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information on the PDGA Disciplinary Process">Disciplinary Process</a></li>
<li id="menu-440" class="menu-path-documents"><a href="/documents?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Complete list of documents currently available at pdga.com">Documents</a></li>
<li id="menu-528" class="menu-path-node-808"><a href="/elections?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information on the PDGA Elections">Elections</a></li>
<li id="menu-492" class="menu-path-node-154"><a href="/IDGC?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information on the International Disc Golf Center">International Disc Golf Center</a></li>
<li id="menu-493" class="menu-path-node-381"><a href="/organizational-documents?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Organizational Documents">Organizational Documents</a></li>
<li id="menu-683" class="menu-path-node-100340"><a href="/points?s=18f3acbca4490cbf2eae40637cd5b9f0">Points</a></li>
<li id="menu-444" class="menu-path-node-739"><a href="/ratings?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Information about PDGA Player Ratings">Ratings</a></li>
<li id="menu-497" class="menu-path-node-208"><a href="/tech-standards?s=18f3acbca4490cbf2eae40637cd5b9f0" title="Technical Standards">Technical Standards</a></li>
</ul>
</li>
</ul>
    </div>
    
  </div>
</div>
    </div>
    <!-- /nav -->

    <!-- top fullwidth -->
        <!-- /top fullwidth -->

    <!-- content -->
    <div id="content">
        <!-- content-left -->
        <div id="content-left">

        	        	<div class="clear"></div>
                        <!-- content-main -->
            <div id="content-main">

				
                <!-- main -->
                <div id="main" class="column">

                    <h1 class="page-title">Karl Johan Hoj Nybo #28903</h1>                                                                                <div class="player_stats-content">
						<div class="profile-header"><h2>Player Info</h2><p class="location"><strong>Location:</strong> Kã¸Benhavn K, Denmark</p><p class="classification"><strong>Classification: </strong> Professional</p><p class="current-rating"><strong>Current Rating:</strong> 1027 <small class="rating-date">(as of 29-Jan-2013)</small></p><p><strong>Upcoming Events:</strong> <a title="Fountain Hills & Scottsdale, AZ&#013;27-Feb to 02-Mar-2013" href="/tournament_results/99307?s=18f3acbca4490cbf2eae40637cd5b9f0">Memorial Championship presented by Discraft</a></div><p class="nav-link mini-controls"><strong>Player Statistics</strong> | <strong><a href="/player_ratings_detail/44378/2012?s=18f3acbca4490cbf2eae40637cd5b9f0">Ratings Detail</a></strong> | <strong><a href="/player_ratings_history/44378/2012?s=18f3acbca4490cbf2eae40637cd5b9f0">Ratings History</a></strong> </p><h2>2012 Player Statistics</h2><p class="year-link">2012&nbsp;&nbsp;|&nbsp; <strong><a href="/player_stats/44378/2011?s=18f3acbca4490cbf2eae40637cd5b9f0">2011</a></strong> &nbsp;|&nbsp; <strong><a href="/player_stats/44378/2010?s=18f3acbca4490cbf2eae40637cd5b9f0">2010</a></strong> &nbsp;|&nbsp; <strong><a href="/player_stats/44378/2009?s=18f3acbca4490cbf2eae40637cd5b9f0">2009</a></strong> &nbsp;|&nbsp; <strong><a href="/player_stats/44378/2008?s=18f3acbca4490cbf2eae40637cd5b9f0">2008</a></strong> &nbsp;|&nbsp; <strong><a href="/player_stats/44378/2007?s=18f3acbca4490cbf2eae40637cd5b9f0">2007</a></strong> &nbsp;|&nbsp; <strong><a href="/player_stats/44378/2006?s=18f3acbca4490cbf2eae40637cd5b9f0">2006</a></strong></p><h3>Season Totals</h3><table class="summary season-stats"><thead><tr><th class="classification">Class</th><th class="tournament-count">Tournaments Played</th><th class="points">Points</th><th class="prize">Prize</th></tr></thead><tbody><tr><td class="classification">Professional</td><td class="tournament-count">7</td><td class="points">5363</td><td class="prize">$3346.00</td></tr></tbody></table><h3>Tournament Results</h3><h4>Open</h4><table class="results"><thead><tr><th class="place">Place</th><th class="points">Points</th><th class="tournament">Tournament</th><th class="dates">Dates</th><th class="total">Total</th><th class="prize">Prize</th></tr></thead><tbody><tr><td class="place">29</td><td class="points">650</td><td class="tournament"><a href="/tournament_results/76135?s=18f3acbca4490cbf2eae40637cd5b9f0">Memorial Championship - Pro</a></td><td class="dates"><span style="display:none">2012-02-29</span>29-Feb to 03-Mar-2012</td><td class="total">222</td><td class="prize"><span style="display: none">250</span>$250</td></tr><tr><td class="place">2</td><td class="points">810</td><td class="tournament"><a href="/tournament_results/78406?s=18f3acbca4490cbf2eae40637cd5b9f0">Copenhagen Open</a></td><td class="dates"><span style="display:none">2012-04-14</span>14-Apr to 15-Apr-2012</td><td class="total">198</td><td class="prize"><span style="display: none">746</span>$746</td></tr><tr><td class="place">2</td><td class="points">278</td><td class="tournament"><a href="/tournament_results/85412?s=18f3acbca4490cbf2eae40637cd5b9f0">DDGU DT 2012 #2</a></td><td class="dates"><span style="display:none">2012-04-21</span>21-Apr to 22-Apr-2012</td><td class="total">205</td><td class="prize"><span style="display: none">123</span>$123</td></tr><tr><td class="place">2</td><td class="points">345</td><td class="tournament"><a href="/tournament_results/78412?s=18f3acbca4490cbf2eae40637cd5b9f0">Sula Open</a></td><td class="dates"><span style="display:none">2012-06-07</span>07-Jun to 10-Jun-2012</td><td class="total">214</td><td class="prize"><span style="display: none">731</span>$731</td></tr><tr><td class="place">10</td><td class="points">2265</td><td class="tournament"><a href="/tournament_results/77432?s=18f3acbca4490cbf2eae40637cd5b9f0">Stockholm Open</a></td><td class="dates"><span style="display:none">2012-06-28</span>28-Jun to 01-Jul-2012</td><td class="total">242</td><td class="prize"><span style="display: none">809</span>$809</td></tr><tr><td class="place">2</td><td class="points">890</td><td class="tournament"><a href="/tournament_results/77435?s=18f3acbca4490cbf2eae40637cd5b9f0">European Championships</a></td><td class="dates"><span style="display:none">2012-08-15</span>15-Aug to 18-Aug-2012</td><td class="total">235</td><td class="prize"><span style="display: none">429</span>$429</td></tr><tr><td class="place">1</td><td class="points">125</td><td class="tournament"><a href="/tournament_results/96667?s=18f3acbca4490cbf2eae40637cd5b9f0">Danish Championships</a></td><td class="dates"><span style="display:none">2012-09-15</span>15-Sep to 16-Sep-2012</td><td class="total">190</td><td class="prize"><span style="display: none">255</span>$255</td></tr></tbody></table><div class="meta"> 
	    	<div class="action-links">

    		<ul class="links inline">
    			<li class="first addthis">
    				
    <div class="addthis"><a href="http://www.addthis.com/bookmark.php"
      onmouseover="return addthis_open(this, '', '[URL]', '[TITLE]')"
      onmouseout="addthis_close()"
      onclick="return addthis_sendto()"><img src="http://s9.addthis.com/button1-share.gif" width="125" height="16" alt="" /></a></div>
    <script type="text/javascript" src="http://s7.addthis.com/js/152/addthis_widget.js"></script>
        			</li>
    		</ul>
    	
    	</div> 
		</div>                                            </div>

                </div>
                <!-- /main -->

            </div>
            <!-- /content-main -->

        </div>
        <!-- /content-left -->

		        <!-- sidebar-right -->
        <div id="sidebar-right" class="column sidebar">
        	<div class="sidebar-right-content">
        		<div class="block block-block " id="block-block-42">
  <div class="block-inner">

    
    <div class="block-content">
      <script type='text/javascript'><!--//<![CDATA[
   var m3_u = (location.protocol=='https:'?'https://www.pdga.com/openx/www/delivery/ajs.php':'http://www.pdga.com/openx/www/delivery/ajs.php');
   var m3_r = Math.floor(Math.random()*99999999999);
   if (!document.MAX_used) document.MAX_used = ',';
   document.write ("<scr"+"ipt type='text/javascript' src='"+m3_u);
   document.write ("?zoneid=29");
   document.write ('&amp;cb=' + m3_r);
   if (document.MAX_used != ',') document.write ("&amp;exclude=" + document.MAX_used);
   document.write (document.charset ? '&amp;charset='+document.charset : (document.characterSet ? '&amp;charset='+document.characterSet : ''));
   document.write ("&amp;loc=" + escape(window.location));
   if (document.referrer) document.write ("&amp;referer=" + escape(document.referrer));
   if (document.context) document.write ("&context=" + escape(document.context));
   if (document.mmm_fo) document.write ("&amp;mmm_fo=1");
   document.write ("'><\/scr"+"ipt>");
//]]>--></script>
    </div>
    
  </div>
</div>
            </div>
        </div>
        <!-- /sidebar-right -->
        
        <div class="clear"></div>

    </div>
    <!-- #content -->

    <!-- bottom -->
    <div id="bottom">

    	<!-- footer adspace -->
    	        <!-- /footer adspace -->

    	<!-- footer 3 column -->
    	    	    	    	<!-- /footer 3 column -->

        <!-- footer -->
        <div id="footer">
            <p>Copyright &copy; 2008-2013. Professional Disc Golf Association. All Rights Reserved. </p>
<p><a href="http://www.pdga.com/tos">Terms of Use and Privacy Policy</a></p>
<div class="block block-block " id="block-block-58">
  <div class="block-inner">

    
    <div class="block-content">
      <p><a href="http://www.facebook.com/pdga" target="_blank" title="facebook"><img src="/files/images/icons/social_facebook.png" alt="facebook" class="social-icon" width="42" height="42"></a><a href="http://www.flickr.com/photos/pdga/collections/" target="_blank" title="flickr"><img src="/files/images/icons/social_flickr.png" alt="flickr" class="social-icon" width="42" height="42"></a><a href="http://twitter.com/pdga" target="_blank" title="twitter"><img src="/files/images/icons/social_twitter.png" alt="twitter" class="social-icon" width="42" height="42"></a><a href="http://www.youtube.com/pdgamedia" target="_blank" title="youtube"><img src="/files/images/icons/social_youtube.png" alt="youtube" class="social-icon" width="42" height="42"></a><a href="/frontpage/feed?s=18f3acbca4490cbf2eae40637cd5b9f0" target="_blank" title="rss feed"><img src="/files/images/icons/social_rss.png" alt="rss" class="social-icon" width="42" height="42"></a></p>
    </div>
    
  </div>
</div>
            <div class="clear"></div>
        </div>
        <!-- /footer -->

    </div>
    <!-- #bottom -->

</div>
<!-- /wrapper -->

<img src="http://www.pdga.com/discussion/cron.php?s=18f3acbca4490cbf2eae40637cd5b9f0&amp;rand=1361528728" alt="" width="1" height="1" border="0" /><script type="text/javascript" src="/sites/all/modules/google_analytics/googleanalytics.js?s=18f3acbca4490cbf2eae40637cd5b9f0"></script>
<script type="text/javascript">var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));</script>
<script type="text/javascript">try{var pageTracker = _gat._getTracker("UA-6108714-1");pageTracker._trackPageview();} catch(err) {}</script>
<!-- Begin comScore Tag -->
<script>
var _comscore = _comscore || [];
_comscore.push({ c1: "2", c2: "14910110" });
(function() {
var s = document.createElement("script"), el = document.getElementsByTagName("script")[0]; s.async = true;
s.src = (document.location.protocol == "https:" ? "https://sb" : "http://b") + ".scorecardresearch.com/beacon.js";
el.parentNode.insertBefore(s, el);
})();
</script>
<noscript>
<img src="http://b.scorecardresearch.com/p?c1=2&amp;c2=14910110&amp;cv=2.0&amp;cj=1" />
</noscript>
<!-- End comScore Tag -->
<!-- Start Quantcast tag -->
<script type="text/javascript" src="//edge.quantserve.com/quant.js?s=18f3acbca4490cbf2ea* Closing connection #0
e40637cd5b9f0"></script>
<script type="text/javascript">_qoptions = { tags:"outdoor enthusiast" }; _qacct="p-31QupbWRoAvms";quantserve();</script>
<noscript>
  <a href="//www.quantcast.com/p-31QupbWRoAvms?s=18f3acbca4490cbf2eae40637cd5b9f0" target="_blank"><img src="http://pixel.quantserve.com/pixel/p-31QupbWRoAvms.gif?tags=outdoor%20enthusiast" height="1" width="1" alt="Quantcast"/></a>
</noscript>
<!-- End Quantcast tag -->
<!-- Compete XL Code for pdga.com -->
<script type="text/javascript">
__compete_code = 'b5046334d003e973e98854e2e9963b5a';
/* Set control variables below this line. */ 
</script>
<script type="text/javascript" src="//c.compete.com/bootstrap/s/b5046334d003e973e98854e2e9963b5a/pdga-com/bootstrap.js?s=18f3acbca4490cbf2eae40637cd5b9f0"></script>
<noscript>
  <img width="1" height="1" src="https://ssl-pdga-com-b50463.c-col.com" alt="Compete XL"/>
</noscript>
<!-- End Compete tag -->
<script src="/sites/all/themes/platform/js/common.js?s=18f3acbca4490cbf2eae40637cd5b9f0" type="text/javascript"></script>
</body>
</html>"""
