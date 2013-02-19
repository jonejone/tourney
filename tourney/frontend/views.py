from django.shortcuts import render
from tourney.tournament.models import Tournament

def index(request):
    t = Tournament.objects.order_by('-start_date')

    tmpl_dict = {
        'tournaments': t}

    return render(
        request,
        'frontend/index.html',
        tmpl_dict)
