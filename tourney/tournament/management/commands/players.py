from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from tourney.tournament.models import Player, Tournament


class Command(BaseCommand):
    args = ''
    help = 'Lists all players with their options'

    option_list = BaseCommand.option_list + (
        make_option('--with-options-only',
            action='store_true',
            dest='options-only',
            default=False,
            help='Only show players that has chosen any options.'),
        )

    def validate_tournament(self, *args, **options):
        # First we must validate tournament
        try:
            t_slug = args[0]
            tournament = Tournament.objects.get(slug=t_slug)
            self.tournament = tournament
        except IndexError:
            raise CommandError('Please enter a tournament slug')
        except Tournament.DoesNotExist:
            raise CommandError('Tournament slug not found')

    def handle(self, *args, **options):
        self.validate_tournament(*args, **options)

        if options['options-only']:
            players = []
            for p in self.tournament.tournamentplayer_set.all():
                if p.options.count() > 0:
                    players.append(p)
        else:
            players = self.tournament.tournamentplayer_set.all()

        for player in players:
            opts = [opt.name for opt in player.options.all()]

            if player.options.count() == 0:
                output = '%(player_name)s - %(total_price)s'
            else:
                output = '%(player_name)s - %(total_price)s - %(options)s'

            output_data = {
                'player_name': player.player.name,
                'options': ', '.join(opts),
                'total_price': '%i %s' % (
                    player.get_player_price(),
                    self.tournament.currency),
            }

            self.stdout.write(output % output_data)
