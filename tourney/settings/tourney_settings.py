import os
import dj_database_url

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..'))

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
    'tourney.tournament.context_processors.tournament',
)

MIDDLEWARE_CLASSES = (
    'djangotoolbox.sites.dynamicsite.DynamicSiteIDMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'tourney.tournament.middleware.TournamentMiddleware',
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.markup',

    'django_extensions',
    'django_nose',
    'django_countries',
    'registration',
    'boto',
    'storages',
    'crispy_forms',
    #'ckeditor',

    'tourney.tournament',
    'tourney.frontend',
)

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"
ROOT_URLCONF = 'tourney.frontend.urls'
#LANGUAGE_CODE = 'nb_NO'
ACCOUNT_ACTIVATION_DAYS = 30

DEBUG = False
if os.environ.get('TOURNEY_DEBUG'):
    DEBUG = True

DATABASES = {'default': dj_database_url.config()}

# S3 configuration
#STATICFILES_STORAGE = 'caddybook.s3utils.StaticRootS3BotoStorage'
#DEFAULT_FILE_STORAGE = 'caddybook.s3utils.MediaRootS3BotoStorage'

if os.environ.get('AWS_ACCESS_KEY_ID'):
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
    AWS_BUCKET_NAME = os.environ['AWS_BUCKET_NAME']
    AWS_BUCKET_URL = 'https://s3.amazonaws.com/%s/' % AWS_BUCKET_NAME
    STATIC_URL = '%sstatic/' % AWS_BUCKET_URL
    MEDIA_URL = '%smedia/' % AWS_BUCKET_URL

ADMINS = (
    ('Jone Eide', 'jone@idev.no'),
)


if os.environ.get('SENDGRID_USERNAME'):
    EMAIL_HOST_USER = os.environ['SENDGRID_USERNAME']
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_PASSWORD = os.environ['SENDGRID_PASSWORD']


CRISPY_TEMPLATE_PACK = 'bootstrap'


