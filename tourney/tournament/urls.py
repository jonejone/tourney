from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    (r'^ckeditor/', include('ckeditor.urls')),
)

urlpatterns += patterns(
    'tourney.tournament.views',
    url(r'^$', 'index', name='tournament-index'),
    url(
        r'^registration/$',
        'registration',
        name='tournament-registration'),
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
