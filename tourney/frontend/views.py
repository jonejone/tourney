from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tourney.tournament.models import Tournament, TournamentAdmin


@login_required
def profile(request):
    tmpl_dict = {}

    # Find tournaments where user is admin
    tournaments = [ta.tournament for ta in \
        request.user.tournamentadmin_set.all()]

    tmpl_dict.update({'tournaments': tournaments})

    # See if we are in a tournament context, use different
    # base template if that is the case
    if hasattr(request, 'tournament'):
        tmpl_dict.update({'extends_tmpl':
            'tournament/tournament_base.html'})
    else:
        tmpl_dict.update({'extends_tmpl':
            'frontend/base.html'})

    return render(
        request, 'frontend/accounts/profile.html', tmpl_dict)


def index(request):
    t = Tournament.objects.order_by('-start_date')

    tmpl_dict = {
        'tournaments': t}

    return render(
        request,
        'frontend/index.html',
        tmpl_dict)
