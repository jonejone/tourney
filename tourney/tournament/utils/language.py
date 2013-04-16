
def default_language():
    from django.contrib.sites.models import Site
    current = Site.objects.get_current()

    try:
        site = current.tournamentsite_set.all()[0]
    except IndexError:
        return ''

    return site.tournament.language
