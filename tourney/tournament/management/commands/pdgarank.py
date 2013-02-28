from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from tourney.tournament.models import Player, Tournament
from tourney.tournament.utils.pdga import PDGARanking


class Command(BaseCommand):
    args = ''
    help = 'Updates player PDGA rank'

    option_list = BaseCommand.option_list + (
        make_option('--updatemissing',
            action='store_true',
            dest='updatemissing',
            default=False,
            help='Accept new players on waiting list based on available spots'),
        )

    def updatemissing(self):
        t = self.tournament
        o = self.stdout
        players = t.tournamentplayer_set.filter(
            player__pdga_number__isnull=False,
            player__pdga_rating__isnull=True)

        if not players:
            o.write('No players to update')
            return

        o.write('Trying to update %i players' \
            % players.count())

        for player in players:
            pdga_rank = PDGARanking(player.player.pdga_number)

            if pdga_rank.rating:
                player.player.pdga_rating = pdga_rank.rating
                player.player.save()

                o.write('- updated to %s for %s (%s)' % (
                    pdga_rank.rating,
                    player.player.name,
                    player.player.pdga_number))
            else:
                o.write('- unable to update %s (%s)' % (
                    player.player.name,
                    player.player.pdga_number))

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

        if options['updatemissing']:
            self.validate_tournament(*args, **options)
            self.updatemissing()
            return

        # Check if player ID is valid
        try:
            player = Player.objects.get(
                id=args[0])
        except Player.DoesNotExist:
            raise CommandError('Player %s does not exist' % args[0])

        # Check if PDGA number is entered for this player
        if not player.pdga_number:
            raise CommandError('Player %s doesnt' % args[0] +
                               ' ' + 'have a PDGA number')

        # Seems we have everything, make call to PDGA
        pdga = PDGARanking(player.pdga_number)

        if pdga.rating:
            player.pdga_rating = pdga.rating
            player.save()
            self.stdout.write('Succesfully updated PDGA rating to' +
                              ' ' + str(pdga.rating) + ' for player ' +
                              player.name)
        else:
            self.stdout.write('Unable to find PDGA rating ' +
                              'for this player')
