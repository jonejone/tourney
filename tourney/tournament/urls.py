from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns(
    'tourney.tournament.views',
    url(r'^$', 'index', name='tournament-index'),
    url(r'^registration/$', 'registration', name='tournament-registration'),
    url(r'^players/$', 'players', name='tournament-players'),
)
