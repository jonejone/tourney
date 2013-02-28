from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    (r'^ckeditor/', include('ckeditor.urls')),

    # The welcome to logged in view
    url(
        r'^accounts/profile/',
        'tourney.frontend.views.profile',
        name='frontend-accounts-profile'),

)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )


urlpatterns += patterns(
    'tourney.frontend.views',
    url(r'^$', 'index', name='frontend-index'),
)
