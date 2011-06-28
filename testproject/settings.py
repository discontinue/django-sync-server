# coding: utf-8
"""
    testproject.settings
    ~~~~~~~~~~~~~~~~~~~~~~

    IMPORTANT:
        You should not edit this file!
        Overwrite settings with a local settings file:
            local_settings.py
        more info:
            http://code.google.com/p/django-sync-server/wiki/WeaveSettings

    Here are not all settings predefined you can use. Please look at the
    django documentation for a full list of all items:
        http://www.djangoproject.com/documentation/settings/

    :copyleft: 2010-2011 by the django-sync-server team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import os
import sys

try:
    #from django_tools.utils import info_print;info_print.redirect_stdout()
    import django
    import weave
except Exception, e:
    import traceback
    print "-" * 79
    sys.stderr.write(traceback.format_exc())
    print "-" * 79
    raise

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'test.db3')
    }
}

TIME_ZONE = "UTC"

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

MEDIA_ROOT = ''

MEDIA_URL = ''

ADMIN_MEDIA_PREFIX = '/media/'

SECRET_KEY = "Make this unique, and don't share it with anybody!"

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

LOGIN_URL = "admin"

ROOT_URLCONF = 'testproject.urls'


TEMPLATE_DIRS = (
    os.path.join(os.path.abspath(os.path.dirname(django.__file__)), "contrib/admin/templates"),
    os.path.join(PROJECT_ROOT, "templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    "weave",
    "south",
)

from weave import app_settings as WEAVE

try:
    from local_settings import *
except ImportError, err:
    msg = (
        "No local_settings.py imported from '%s' !"
        " (Original error was: %s)\n"
    ) % (os.getcwd(), err)
    sys.stderr.write(msg)
