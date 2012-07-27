# coding:utf-8

'''
    misc views
    ~~~~~~~~~~
    
    Created on 27.03.2010
    
    Due to Mozilla Weave supporting Recaptcha solely, we have to stick with it until
    they decide to change the interface to pluggable captchas.

    @license: GNU GPL v3 or above, see LICENSE for more details.
    @copyleft: 2010-2012 by the django-sync-server team, see AUTHORS for more details.
'''

import time

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

# django-sync-server own stuff
from weave import Logging, VERSION_STRING
from weave.decorators import weave_assert_version, debug_sync_request
from weave.models import Wbo


logger = Logging.get_logger()


@debug_sync_request
@weave_assert_version(("1.0", "1.1"))
@csrf_exempt
def captcha(request, version):
    if settings.WEAVE.DONT_USE_CAPTCHA == True:
        logger.warn("You should activate captcha!")#
        return HttpResponse("Captcha support is disabled.")

    # Check for aviability of recaptcha 
    # (can be found at: http://pypi.python.org/pypi/recaptcha-client)
    try:
        from recaptcha.client.captcha import displayhtml
    except ImportError:
        logger.error("Captcha requested but unable to import the 'recaptcha' package!")
        return HttpResponse("Captcha support disabled due to missing Python package 'recaptcha'.")
    if not getattr(settings.WEAVE, "RECAPTCHA_PUBLIC_KEY"):
        logger.error("Trying to create user but settings.WEAVE.RECAPTCHA_PUBLIC_KEY not set")
        raise ImproperlyConfigured
    # Send a simple HTML to the client. It get's rendered inside the Weave client.
    return HttpResponse("<html><body>%s</body></html>" % displayhtml(settings.WEAVE.RECAPTCHA_PUBLIC_KEY))


def info_page(request):
    server_url = request.build_absolute_uri(request.path)
    if not server_url.endswith("/"):
        # sync setup dialog only accept the server url if it's ends with a slash
        server_url += "/"

    context = {
        "title": "django-sync-server - info page",
        "request": request,
        "weave_version": VERSION_STRING,
        "server_url":server_url,
    }

    if request.user.is_authenticated() and request.user.is_active:
        start_time = time.time()

        payload_queryset = Wbo.objects.filter(user=request.user.id).only("payload")

        wbo_count = 0
        payload_size = 0
        for item in payload_queryset.iterator():
            wbo_count += 1
            payload_size += len(item.payload)

        modified_queryset = Wbo.objects.filter(user=request.user.id).only("modified")
        try:
            latest = modified_queryset.latest("modified").modified
        except Wbo.DoesNotExist:
            # User hasn't used sync, so no WBOs exist from him
            latest = None
            oldest = None
        else:
            oldest = modified_queryset.order_by("modified")[0].modified

        duration = time.time() - start_time

        context.update({
            "wbo_count": wbo_count,
            "payload_size": payload_size,
            "duration": duration,
            "latest_modified": latest,
            "oldest_modified": oldest,
        })

    return render_to_response("weave/info_page.html", context, context_instance=RequestContext(request))
