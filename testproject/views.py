#coding:utf-8

from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required


def absolute_uri(request, view_name, **kwargs):
    url = reverse(view_name, kwargs=kwargs)
    absolute_uri = request.build_absolute_uri(url)
    return absolute_uri


@login_required
def url_info(request):

    server_url = request.build_absolute_uri("weave")
    if not server_url.endswith("/"):
        # sync setup dialog only accept the server url if it's ends with a slash
        server_url += "/"

    context = {
        "title": "weave testproject url info",
        "server_url": server_url,
        "register_check_url": absolute_uri(request, "weave-register_check", username=request.user.username),
        "info_url": absolute_uri(request, "weave-info", version="1.0", username=request.user.username),
    }
    return render_to_response("testproject/url_info.html", context)
