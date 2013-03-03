from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    (r'^ckeditor/', include('ckeditor.urls')),
    (r'^accounts/', include('tourney.frontend.registration_urls')),

    # The welcome to logged in view
    url(
        r'^accounts/profile/',
        'tourney.frontend.views.profile',
        name='tournament-accounts-profile'),

    url(
        r'^edit/$',
        'tourney.tournament.views.edit_tournament',
        name='tournament-admin-edit'),

)


if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )


urlpatterns += patterns(
    'tourney.tournament.views',
    url(r'^$', 'index', name='tournament-index'),
    url(
        r'^registration/embed/$',
        'registration',
        {'embed': True},
        name='tournament-registration-embed'),
    url(
        r'^registration/$',
        'registration',
        name='tournament-registration'),
    url(
        r'^registration-complete/embed/$',
        'registration_complete',
        {'embed': True},
        name='tournament-registration-complete-embed'),

    url(
        r'^registration-complete/$',
        'registration_complete',
        name='tournament-registration-complete'),

    url(
        r'^ajax/check-pdga-number/$',
        'check_pdga_number',
        name='tournament-ajax-check-pdga-number'),

    url(
        r'^players/$',
        'players',
        name='tournament-players'),

    url(
        r'^ajax/player-action/$',
        'ajax_player_action',
        name='tournament-ajax-player-action'),

    url(
        r'^players/waiting-list/$',
        'waiting_list',
        name='tournament-waiting-list'),

    url(
        r'^players/embed/$',
        'players',
        {'embed': True},
        name='tournament-players-embed'),

    url(
        r'^(?P<slug>[-\w]+)/$',
        'page',
        name='tournament-page'),

    url(
        r'^(?P<slug>[-\w]+)/edit/$',
        'page_edit',
        name='tournament-page-edit'),

    url(
        r'^news/create/$',
        'news_edit',
        name='tournament-news-create'),

    url(
        r'^news/(?P<slug>[-\w]+)/$',
        'news_item',
        name='tournament-news-item'),

    url(
        r'^news/(?P<slug>[-\w]+)/edit/$',
        'news_edit',
        name='tournament-news-edit'),


)

urlpatterns += patterns(
    'tourney.tournament.ajaxviews',
    url(
        r'^ajax/update-player-paid/$',
        'update_player_paid',
        name='tournament-ajax-update-player-paid'),
)
