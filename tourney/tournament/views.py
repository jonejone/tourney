from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.core.context_processors import csrf

from django_countries.countries import OFFICIAL_COUNTRIES
from datetime import datetime

from .forms import RegistrationForm, TournamentPageForm, TournamentNewsItemForm
from .models import (TournamentPage,
                     TournamentNewsItem,)
from .utils.pdga import PDGARanking


FLIPPED_COUNTRIES = dict([(x, y) for y, x in OFFICIAL_COUNTRIES.items()])


def players(request, embed=False):

    extends_tmpl = 'tournament/tournament_base.html'

    if embed:
        extends_tmpl = 'tournament/embed_base.html'

    tmpl_dict = {
        'csrf': csrf(request),
        'extends_tmpl': extends_tmpl,
        'is_embedded': embed,
    }

    return render(
        request, 'tournament/players.html', tmpl_dict)


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


def registration_complete(request, embed=False):
    extends_tmpl = 'tournament/tournament_base.html'

    if embed:
        extends_tmpl = 'tournament/embed_base.html'

    tmpl_dict = {'extends_tmpl': extends_tmpl}

    return render(
        request,
        'tournament/registration-complete.html',
        tmpl_dict)


def registration(request, embed=False):
    tournament = request.tournament
    extends_tmpl = 'tournament/tournament_base.html'

    if embed:
        extends_tmpl = 'tournament/embed_base.html'


    if request.method == 'POST':
        form = RegistrationForm(
            request.POST,
            tournament=tournament)
        if form.is_valid():
            form.save()
            if embed:
                return HttpResponseRedirect(reverse(
                    'tournament-registration-complete-embed'))
            else:
                return HttpResponseRedirect(reverse(
                    'tournament-registration-complete'))
    else:
        form = RegistrationForm(
            tournament=tournament)

    tmpl_dict = {
        'form': form,
        'extends_tmpl': extends_tmpl,
        'is_embedded': embed,
    }

    if tournament.registration_stages:
        tmpl_dict.update({
            'current_stage': tournament.get_registration_stage()
        })

    response = render(
        request, 'tournament/registration.html', tmpl_dict)

    # We need this header so IE will allow third-party
    # cookies (required for the embedded iframes)
    response['P3P'] = "CP=\"CAO PSA OUR\""

    return response



def index(request):
    try:
        page = request.tournament.tournamentpage_set.get(
            slug='frontpage')
    except TournamentPage.DoesNotExist:
        page = None

    news_items = request.tournament.tournamentnewsitem_set.filter(
        is_published=True).order_by('-published')

    tmpl_dict = {
        'page': page,
        'news_items': news_items,
    }

    return render(
        request,
        'tournament/index.html',
        tmpl_dict)


def page_edit(request, slug):
    page = get_object_or_404(
        TournamentPage, slug=slug, tournament=request.tournament)

    if request.method == 'POST':
        form = TournamentPageForm(
            request.POST, instance=page)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse(
                'tournament-page', args=[page.slug, ]))
    else:
        form = TournamentPageForm(instance=page)

    tmpl_dict = {
        'page': page,
        'form': form,
        'sidebar': False,
    }

    return render(
        request, 'tournament/page_edit.html', tmpl_dict)


def page(request, slug):
    page = get_object_or_404(
        TournamentPage, slug=slug, tournament=request.tournament)

    tmpl_dict = {
        'page': page
    }

    return render(
        request, 'tournament/page.html', tmpl_dict)


def news_item(request, slug):

    lookup_args = {
        'slug': slug,
    }

    if not request.user.is_authenticated():
        lookup_args.update({
            'is_published': True})

    try:
        item = request.tournament.tournamentnewsitem_set.get(
            **lookup_args)
    except TournamentNewsItem.DoesNotExist:
        raise Http404

    tmpl_dict = {
        'news_item': item,
    }

    return render(
        request,
        'tournament/news_item.html',
        tmpl_dict)


def news_edit(request, slug=None):
    if not request.user.is_authenticated():
        return HttpResponse('No access!')

    create_new = True
    kwargs = {}
    tmpl_dict = {}

    if slug:
        news_item = get_object_or_404(
            TournamentNewsItem,
            tournament=request.tournament,
            slug=slug)

        kwargs.update({'instance': news_item})
        tmpl_dict.update({'news_item': news_item})
        create_new = False

    if request.method == 'POST':
        form = TournamentNewsItemForm(request.POST, **kwargs)

        if form.is_valid():
            item = form.save(commit=False)

            if create_new:
                item.user = request.user
                item.tournament = request.tournament
                item.created = datetime.now()
                item.slug = slugify(item.title)

            if item.is_published and item.published is None:
                item.published = datetime.now()

            item.save()
            return HttpResponseRedirect(reverse(
                'tournament-news-item', args=[item.slug, ]))
    else:
        form = TournamentNewsItemForm(**kwargs)

    tmpl_dict.update({
        'form': form,
        'sidebar': None,
    })

    return render(
        request,
        'tournament/news_item_edit.html',
        tmpl_dict)
