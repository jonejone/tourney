
def tournament(request):
    context = {}

    if request.tournament:
        pages = request.tournament.tournamentpage_set.order_by(
            'navigation_position')

        context.update({
            'tournament': request.tournament,
            'tournament_pages': pages,})

    return context
