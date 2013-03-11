from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from tourney.tournament.models import Player, Tournament


class Command(BaseCommand):
    args = ''
    help = 'Lists all players with their options'

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

        players = self.tournament.tournamentplayer_set.all()

        for player in players:
            options = [opt.name for opt in player.options.all()]

            if player.options.count() == 0:
                output = '%(player_name)s - %(total_price)s'
            else:
                output = '%(player_name)s - %(total_price)s - %(options)s'

            output_data = {
                'player_name': player.player.name,
                'options': ', '.join(options),
                'total_price': '%i %s' % (
                    player.get_player_price(),
                    self.tournament.currency),
            }

            self.stdout.write(output % output_data)
