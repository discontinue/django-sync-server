# coding:utf-8

"""   
    django-sync-server app settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~
    All own settings for the django-sync-server app.
    
    **IMPORTANT:**
        You should not edit this file!
        Overwrite settings with a local settings file:
            local_settings.py
        more info:
            http://code.google.com/p/django-sync-server/wiki/WeaveSettings
    
    :copyleft: 2010-2011 by the django-sync-server team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


# Must be obtained from http://recaptcha.net/ by registering an account.
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''

# Create users without any captcha.
# NOT RECOMMENDED! Spam bots can flooding your server!
DONT_USE_CAPTCHA = False

BASICAUTH_REALM = "django-sync-server"

# Disable own basicauth login?
# If True: basicauth would be deactivated and every login request over 
# django-sync-server own views would be denied.
# The user must login in a other way, before using firefox-sync
# e.g. use the django admin login page.
DISABLE_LOGIN = False

# Log request/reponse debug information
DEBUG_REQUEST = False
