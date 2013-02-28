"""
Modified backend (URLconf) for 'django-registration'
"""


from django.conf.urls.defaults import patterns, url, include
from django.views.generic import TemplateView

from registration.views import activate
from registration.views import register


class ActivationCompleteView(TemplateView):
    template_name = 'registration/activation_complete.html'


class RegistrationCompleteView(TemplateView):
    template_name = 'registration/registration_complete.html'


class RegistrationClosedView(TemplateView):
    template_name = 'registration/registration_closed.html'


urlpatterns = patterns(
    '',

    url(r'^activate/complete/$',
        ActivationCompleteView.as_view(),
        name='registration_activation_complete'),

    # Activation keys get matched by \w+ instead of the more specific
    # [a-fA-F0-9]{40} because a bad activation key
    # should still get to the view;
    # that way it can return a sensible "invalid key" message instead of a
    # confusing 404.
    url(r'^activate/(?P<activation_key>\w+)/$', activate,
        {'backend': 'registration.backends.default.DefaultBackend'},
        name='registration_activate'),

    url(r'^register/$', register,
        {'backend': 'registration.backends.default.DefaultBackend'},
        name='registration_register'),

    url(r'^register/complete/$', RegistrationCompleteView.as_view(),
        name='registration_complete'),

    url(r'^register/closed/$', RegistrationClosedView.as_view(),
        name='registration_disallowed'),

    (r'', include('registration.auth_urls')),
)
