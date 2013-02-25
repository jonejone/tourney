from django.core.management.base import BaseCommand, CommandError
from tourney.tournament.models import Tournament, TournamentPlayer
from optparse import make_option

class Command(BaseCommand):
    args = '<tournament_slug> --sync'
    help = 'Manage waiting list'

    option_list = BaseCommand.option_list + (
        make_option('--accept-player',
            action='store',
            dest='acceptplayer',
            default=False,
            help='Accept player into tournament and remove from waiting list'),
        make_option('--accept',
            action='store_true',
            dest='accept',
            default=False,
            help='Accept new players on waiting list based on available spots'),
        )

    def handle(self, *args, **options):
        try:
            t_slug = args[0]
            tournament = Tournament.objects.get(slug=t_slug)
            self.tournament = tournament
        except IndexError:
            raise CommandError('Please enter a tournament slug')
        except Tournament.DoesNotExist:
            raise CommandError('Tournament slug not found')

        if options['acceptplayer']:
            self.accept(options['acceptplayer'])
        elif options['accept']:
            self.accept()
        else:
            self.print_waiting_list()

    def accept(self, player_id=None):

        if player_id:
            try:
                tp = self.tournament.tournamentplayer_set.get(
                    id=player_id)
            except TournamentPlayer.DoesNotExist:
                raise CommandError('Not a valid player ' +
                    'in this tournament')

            players = [tp, ]
        else:
            players = self.tournament.tournamentplayer_set.filter(
                is_waiting_list=True).order_by('-registered')

        spots = self.tournament.get_available_spots()

        if spots == 0:
            raise CommandError('This tournament does not have'
                + ' any free spots for taking.')

        if len(players) > spots:
            players = players[:spots]

        for player in players:
           player.accept_player()

        self.stdout.write('Accepted %i players' % len(players))

    def print_waiting_list(self):
        players = self.tournament.tournamentplayer_set.filter(
            is_waiting_list=True)

        print 'Waiting list for %s, %i players, %i open spots' % (
            self.tournament.name,
            players.count(),
            self.tournament.get_available_spots())

        for player in players:
            print '- %s [%i]' % (player.player.name, player.id)
