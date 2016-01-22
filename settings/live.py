from settings import *

BACKUPDB_DIRECTORY = os.environ['BACKUP_DIR']
MEDIA_ROOT = os.environ['MEDIA_ROOT']
STATIC_ROOT = os.environ['STATIC_ROOT']

DEBUG = False

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = ''
EMAIL_PORT = 465
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = 'no-reply@floodlightproject.org'

DATABASES = {'default': dj_database_url.config()}
DATABASES['default']['ATOMIC_REQUESTS'] = True

HAYSTACK_CONNECTIONS['default']['URL'] = 'http://127.0.0.1:8983/solr/floodlight_live'

RAVEN_CONFIG = {
    'dsn': 'https://223a9ba8b85b4ba1b5ae2d09831e77e4:8d9c8e76d4854806b3cbf728e2276045@sentry.fusionbox.com/67'
}

TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
TEMPLATES[0]['OPTIONS']['loaders'] = (
    ('django.template.loaders.cached.Loader', TEMPLATES[0]['OPTIONS']['loaders']),
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'floodlightproject',
    }
}

FILER_STORAGES['public']['main']['OPTIONS']['location'] = os.path.abspath(os.path.join(MEDIA_ROOT, 'filer'))
FILER_STORAGES['public']['thumbnails']['OPTIONS']['location'] = os.path.abspath(os.path.join(MEDIA_ROOT, 'filer_thumbnails'))

COMPRESS_PRECOMPILERS = (
    ('text/less', 'node_modules/.bin/lessc {infile} {outfile}'),
)

ALLOWED_HOSTS = [
    'www.floodlightproject.org',
    'new.floodlightproject.org',
]
