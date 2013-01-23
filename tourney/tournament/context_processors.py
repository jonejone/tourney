
def tournament(request):
    context = {}

    if request.tournament:
        pages = request.tournament.tournamentpage_set.filter(
            show_in_navigation=True).order_by(
                'navigation_position')

        context.update({
            'tournament': request.tournament,
            'tournament_pages': pages,})

    return context
