from tourney.tournament.models import TournamentPage


def tournament(request):
    context = {}

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

    if hasattr(request, 'is_tournament_admin'):
        context.update({'is_tournament_admin':
            request.is_tournament_admin})

    return context
