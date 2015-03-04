
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from tourney.tournament.models import Player, Tournament


class Command(BaseCommand):
    help = 'Show status of registered players'

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

        is_full = self.tournament.is_registration_full()
        available = self.tournament.get_available_spots()
        pending_payment = self.tournament.tournamentplayer_set.filter(
            is_pending_payment=True).count()


        self.stdout.write('Status for %s' % self.tournament.name)

        if is_full:
            self.stdout.write('- Tournament is full')
        else:
            self.stdout.write('- Tournament is not full, %s spots available' % available)

        self.stdout.write('- Registered players: %i' % self.tournament.get_player_list_count())
        self.stdout.write('- Players awaiting payment: %i' % pending_payment)
        self.stdout.write('- Players on waiting list: %i' % \
            self.tournament.get_waiting_list_count())
