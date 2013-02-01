from django.core.management.base import BaseCommand, CommandError

from tourney.tournament.models import Player
from tourney.tournament.utils.pdga import PDGARanking


class Command(BaseCommand):
    args = '<player_id>'
    help = 'Updates player PDGA rank'

    def handle(self, *args, **kwargs):
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
                              ' ' + pdga.rating + ' for player ' +
                              player.name)
        else:
            self.stdout.write('Unable to find PDGA rating ' +
                              'for this player')
