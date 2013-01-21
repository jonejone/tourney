from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import simplejson

from django_countries.countries import OFFICIAL_COUNTRIES

from .forms import RegistrationForm, TournamentPageForm
from .models import TournamentPlayer, Tournament, TournamentPage
from .utils.pdga import PDGARanking


FLIPPED_COUNTRIES = dict([(x,y) for y,x in OFFICIAL_COUNTRIES.items()])


def players(request):
    return render(request,
        'tournament/players.html')


def check_pdga_number(request):

    num = request.GET.get('pdga_number', False)
    json_data = {
        'success': False,
    }

    if num:
        pdga = PDGARanking(num)
        if pdga.rating:
            # Make some checks on location to
            # auto-detect country as well
            country_code = None

            if pdga.location:
                country_search = pdga.location.split(
                    ', ')[1].upper()
                country_code = FLIPPED_COUNTRIES.get(country_search, None)
                if country_code:
                    json_data.update({'country_code': country_code})

            json_data.update({
                'rating': pdga.rating,
                'name': pdga.name,
                'success': True})

    return HttpResponse(
        simplejson.dumps(json_data),
        mimetype='application/json')


def registration_complete(request):
    return render(
        request,
        'tournament/registration-complete.html')


def registration(request):
    tournament = request.tournament

    if request.method == 'POST':
        form = RegistrationForm(
            request.POST,
            tournament=tournament)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse(
                'tournament-registration-complete'))
    else:
        form = RegistrationForm(
            tournament=tournament)

    tmpl_dict = {
        'form': form,
    }

    if tournament.registration_stages:
        tmpl_dict.update({
            'current_stage': tournament.get_registration_stage()
        })

    return render(request,
        'tournament/registration.html', tmpl_dict)


def index(request):
    return render(request,
        'tournament/index.html')


def page_edit(request, slug):
    page = get_object_or_404(TournamentPage,
        slug=slug, tournament=request.tournament)

    if request.method == 'POST':
        form = TournamentPageForm(
            request.POST, instance=page)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse(
                'tournament-page', args=[page.slug,]))
    else:
        form = TournamentPageForm(instance=page)

    tmpl_dict = {
        'page': page,
        'form': form,
    }

    return render(request,
        'tournament/page_edit.html', tmpl_dict)


def page(request, slug):
    page = get_object_or_404(TournamentPage,
        slug=slug, tournament=request.tournament)

    tmpl_dict = {
        'page': page
    }

    return render(request,
        'tournament/page.html', tmpl_dict)
