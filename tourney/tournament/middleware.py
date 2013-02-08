from django.conf import settings
from django.contrib.sites.models import Site
from .models import Tournament, TournamentSite, TournamentAdmin


class TournamentMiddleware:
    def process_request(self, request):

        current = Site.objects.get_current()

        try:
            ts = TournamentSite.objects.get(
                site=current)
        except TournamentSite.DoesNotExist:
            pass
        else:
            tournament = ts.tournament

            request.tournament = tournament
            request.urlconf = 'tourney.tournament.urls'

            # See if current user is admin
            request.is_tournament_admin = False

            if request.user.is_authenticated():
                if request.user.is_staff:
                    request.is_tournament_admin = True

                try:
                    admin = request.user.tournamentadmin_set.get(
                        tournament=request.tournament)
                except TournamentAdmin.DoesNotExist:
                    pass
                else:
                    request.is_tournament_admin = True
