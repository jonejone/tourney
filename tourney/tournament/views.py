from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _

from django_countries.countries import OFFICIAL_COUNTRIES
from datetime import datetime

from .forms import (
    RegistrationForm,
    TournamentPageForm,
    TournamentForm,
    TournamentPlayerForm,
    EmailPlayersForm,
    TournamentRegistrationForm,
    TournamentNewsItemForm)

from .models import (
    TournamentPage,
    TournamentPlayer,
    NoTournamentSpotsException,
    TournamentNewsItem)

from .utils.pdga import PDGARanking


FLIPPED_COUNTRIES = dict([(x, y) for y, x in OFFICIAL_COUNTRIES.items()])


@login_required
@csrf_exempt
def ajax_player_action(request):
    t = request.tournament

    # User must be admin
    if not request.is_tournament_admin:
        raise Http404

    # We only accept POST requests
    if request.method != 'POST':
        raise Http404

    # Our allowed actions for a player
    allowed_actions = [
        'waiting-list-accept',
        'waiting-list-remove',
    ]

    action = request.POST.get('action')
    player_id = request.POST.get('tournamentplayer_id')
    json_data = {
        'success': False,
    }

    try:
        player = request.tournament.tournamentplayer_set.get(
            id=player_id)
    except TournamentPlayer.DoesNotExist:
        raise Http404

    if action not in allowed_actions:
        raise Http404

    if action == 'waiting-list-remove':
        player.delete()
        json_data.update({
            'success': True,
            'removed': True})

    if action == 'waiting-list-accept':
        try:
            player.accept_player()
        except NoTournamentSpotsException:
            json_data.update({'error': 'No available tournament spots'})
        else:
            json_data.update({
                'success': True,
                'removed': True})

    # Add some counters
    json_data.update({
        'updater_data': {
            'wildcard-spots': t.wildcard_spots,
            'available-spots': t.get_available_spots(),
            'waiting-list-count': t.get_waiting_list_count(),
            'player-list-count': t.get_player_list_count(),
            'max-players': t.max_players,
        }
    })

    return HttpResponse(
        simplejson.dumps(json_data),
        mimetype='application/json')


def options(request):
    return render(
        request,
        'tournament/admin/options.html')


def waiting_list(request, embed=False):
    tournament = request.tournament
    players = tournament.tournamentplayer_set.filter(
        is_waiting_list=True).order_by('registered')

    tmpl_dict = {
        'players': players,
        'is_embedded': embed,
        'extends_tmpl': 'tournament/tournament_base.html',
        'csrf': csrf(request),
    }

    if embed:
        tmpl_dict.update({
            'extends_tmpl': 'tournament/embed_base.htm'})

    return render(
        request,
        'tournament/players/waiting-list.html',
        tmpl_dict)


@login_required
def email_players(request):

    t = request.tournament

    if not request.is_tournament_admin:
        raise Http404

    tmpl_dict = {}

    if request.method == 'POST':
        form = EmailPlayersForm(request.POST)
        if form.is_valid():
            form.save(tournament=t)

            messages.success(
                request,
                _('Email has been sent out according to your selections.'))

            return HttpResponseRedirect(reverse(
                'tournament-admin-email-players'))
    else:
        form = EmailPlayersForm()

    if t.tournament_admin_email:
        form.fields['sender'].initial = t.tournament_admin_email

    form.fields['email_player_list'].label = \
        'Email accepted players (%i)' % t.get_player_list_email_count()

    form.fields['email_waiting_list'].label = \
        'Email players on waiting list (%i)' % t.get_waiting_list_email_count()

    tmpl_dict.update({
        'form': form})

    return render(
        request,
        'tournament/admin/email-players.html',
        tmpl_dict)


@login_required
def edit_tournament(request):

    if not request.is_tournament_admin:
        raise Http404

    if request.method == 'POST':
        form = TournamentForm(
            request.POST,
            instance=request.tournament)

        if form.is_valid():
            t = form.save()
            messages.success(
                request,
                _('Tournament has been updated.'))
            return HttpResponseRedirect(reverse(
                'tournament-admin-edit'))
    else:
        form = TournamentForm(
            instance=request.tournament)

    tmpl_dict = {
        'form': form,
    }

    return render(
        request,
        'tournament/admin/edit-tournament.html',
        tmpl_dict)


def player_edit_registration(request, tp_id):

    # User must be admin
    if not request.is_tournament_admin:
        raise Http404

    try:
        tp = request.tournament.tournamentplayer_set.get(
            id=tp_id)
    except TournamentPlayer.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = TournamentRegistrationForm(
            request.POST,
            instance=tp)

        if form.is_valid():
            tp = form.save()

            messages.success(
                request,
                _('Tournament registration has been updated.'))

            return HttpResponseRedirect(reverse(
                'tournament-registration-edit', args=[tp.id]))

    else:
        form = TournamentRegistrationForm(instance=tp)

    tmpl_dict = {
        'form': form,
        'player': tp,
    }

    return render(
        request,
        'tournament/admin/edit-registration.html',
        tmpl_dict)


def player_edit(request, tp_id):

    # User must be admin
    if not request.is_tournament_admin:
        raise Http404

    try:
        tp = request.tournament.tournamentplayer_set.get(
            id=tp_id)
    except TournamentPlayer.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = TournamentPlayerForm(
            request.POST,
            instance=tp.player)

        if form.is_valid():
            player = form.save()

            messages.success(
                request,
                _('Tournament player has been updated.'))

            return HttpResponseRedirect(reverse(
                'tournament-player-edit', args=[tp.id]))
    else:
        form = TournamentPlayerForm(instance=tp.player)

    tmpl_dict = {
        'form': form,
        'player': tp,
    }

    return render(
        request,
        'tournament/admin/edit-player.html',
        tmpl_dict)


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

            was_full = tournament.is_registration_full()

            tp = form.save()

            # Redirect to Paypal if payments is turned on
            if tournament.enable_payments:
                tp.is_pending_payment = True
                tp.save()
                url = tp.get_paypal_redirect_url()
                return HttpResponseRedirect(url)

            if was_full:
                tp.is_waiting_list = True
                tp.save()
            else:
                tp.send_registration_email()

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


def paypal_return(request):
    import paypalrestsdk
    tournament = request.tournament
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    tp = tournament.tournamentplayer_set.get(
        paypal_payment_id=payment_id)

    tp.paypal_payer_id = payer_id
    tp.save()

    paypal_api = tp.get_paypal_api()

    payment = paypalrestsdk.Payment.find(payment_id, api=paypal_api)
    is_full = tournament.is_registration_full()

    if payment.execute({'payer_id': payer_id}):
        tp.is_pending_payment = False
        tp.is_paid = True

        if is_full:
            tp.is_waiting_list = True
        else:
            tp.send_registration_email()

        tp.save()

        return HttpResponseRedirect(reverse(
            'tournament-registration-complete'))
    else:
        return HttpResponse('Unable to execute payment')



def paypal_cancel(request):
    pass


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
