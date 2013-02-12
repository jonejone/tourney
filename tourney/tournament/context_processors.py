from tourney.tournament.models import TournamentPage
from django.conf import settings


def tournament(request):
    context = {}

    ga_account = None

    if hasattr(settings, 'GOOGLE_ANALYTICS_ACCOUNT'):
        ga_account = settings.GOOGLE_ANALYTICS_ACCOUNT

    if hasattr(request, 'tournament'):
        pages = request.tournament.tournamentpage_set.filter(
            show_in_navigation=True).order_by(
                'navigation_position')

        context.update({
            'tournament': request.tournament,
            'tournament_pages': pages, })

        # See if we have a sidebar page
        try:
            sidebar = request.tournament.tournamentpage_set.get(
                slug='sidebar')
        except TournamentPage.DoesNotExist:
            pass
        else:
            context.update({'sidebar': sidebar})

        if request.tournament.google_analytics_account:
            ga_account = request.tournament.google_analytics_account

    if hasattr(request, 'is_tournament_admin'):
        context.update({'is_tournament_admin':
            request.is_tournament_admin})

    if ga_account:
        context.update({
            'google_analytics_account': ga_account})

    return context
