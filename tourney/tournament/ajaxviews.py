from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils import simplejson

from tourney.tournament.models import TournamentPlayer


def update_player_paid(request):

    if not hasattr(request, 'is_tournament_admin'):
        raise Http404

    is_paid = request.POST.get('is_paid', None)
    tp_id = request.POST.get('tp_id', None)

    if not tp_id or not is_paid:
        raise Http404

    try:
        tp = request.tournament.tournamentplayer_set.get(
            id=tp_id)
    except TournamentPlayer.DoesNotExist:
        raise Http404

    if is_paid == '1':
        tp.is_paid = True
    else:
        tp.is_paid = False

    tp.save()

    response_dict = {
        'success': True,
    }

    return HttpResponse(simplejson.dumps(response_dict),
        mimetype='application/javascript')

