from django.conf import settings
from django.contrib.sites.models import Site
from .models import Tournament, TournamentSite, TournamentAdmin

from localeurl import utils


class TournamentMiddleware:
    def process_request(self, request):
        # See if we can find a tournament
        # attached to our current site
        current = Site.objects.get_current()

        try:
            ts = TournamentSite.objects.get(
                site=current)
        except TournamentSite.DoesNotExist:
            pass
        else:
            # Tournament was found, lets add it to our
            # request object as well as change to
            # tournament-specific urlconf.
            request.tournament = ts.tournament
            request.urlconf = 'tourney.tournament.urls'


class TournamentAdminMiddleware:
    def process_request(self, request):
        # Only applicable if we are in a
        # tournament context
        if hasattr(request, 'tournament'):
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


class TournamentLanguageMiddleware:
    def process_request(self, request):
        # Only applicable if we are in a
        # tournament context
        if hasattr(request, 'tournament'):
            # By setting request.LANGUAGE_CODE, the localeurl
            # lib we are using will pick it up as the currently
            # active language.
            request.LANGUAGE_CODE = request.tournament.language_code
