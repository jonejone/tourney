from django.conf import settings
from tourney.tournament.models import Tournament

class TournamentMiddleware:
    def process_request(self, request):
        if settings.TOURNAMENT_ID:
            tournament = Tournament.objects.get(
                id=settings.TOURNAMENT_ID)

            request.tournament = tournament
