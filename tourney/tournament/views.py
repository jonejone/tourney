from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings

from tourney.tournament.models import Tournament
from .forms import RegistrationForm

def get_settings_tournament():
    return Tournament.objects.get(
        id=settings.TOURNAMENT_ID)


def players(request):
    pass


def registration(request):
    tournament = get_settings_tournament()

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            p = form.save()
            return HttpResponseRedirect(
                '/registration-complete/')
    else:
        form = RegistrationForm()

    tmpl_dict = {
        'tournament': tournament,
        'form': form,
    }

    return render(request,
        'tournament/registration.html', tmpl_dict)


def index(request):
    tournament = get_settings_tournament()

    tmpl_dict = {
        'tournament': tournament,
    }

    return render(request,
        'tournament/index.html', tmpl_dict)
