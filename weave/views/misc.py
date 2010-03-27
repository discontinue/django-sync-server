# coding:utf-8

'''
Created on 27.03.2010

    @license: GNU GPL v3 or above, see LICENSE for more details.
    @copyleft: 2010 by the django-weave team, see AUTHORS for more details.
'''
# Due to Mozilla Weave supporting Recaptcha solely, we have to stick with it until
# they decide to change the interface to pluggable captchas.
from recaptcha.client.captcha import displayhtml

from django.conf import settings
from django.contrib.csrf.middleware import csrf_exempt
from django.http import HttpResponse

# django-weave own stuff
from weave import Logging

logger = Logging.get_logger()

@csrf_exempt
def captcha(request, version):
    # Send a simple HTML to the client. It get's rendered inside the Weave client.
    return HttpResponse("<html><body>%s</body></html>" % displayhtml(settings.RECAPTCHA_PUBLIC_KEY))
    