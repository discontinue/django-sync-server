# coding: utf-8

"""
    Info:
    ~~~~~
    to debug the output in a browser: add "?debug=1" to a url.
    To reformat the payload: add "?debug=2" to a url.
    (This works only if settings.DEBUG==True)
"""

import sys
import struct
import logging

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.3, 2.4 fallback.

#try:
#    import json # New in Python v2.6
#except ImportError:
#    from django.utils import simplejson as json

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        sys.stderr.write("Error: json (or simplejson) module is needed")
        sys.exit(1)

from django.conf import settings
from django.http import HttpResponse

from weave_project.weave.utils import timestamp, datetime2epochtime, cut, WeaveTimestamp

logging.basicConfig(level=logging.DEBUG)


def assert_username(debug=False):
    """ Check if the username from the url is logged in. """
    def _inner(view_function):
        @wraps(view_function)
        def _check_user(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated():
                msg = "Permission denied for anonymous user. Please log in."
                if debug:
                    logging.debug(msg)
                raise PermissionDenied(msg)

            username = kwargs["username"]
            if user.username != username:
                msg = "Wrong user!"
                if debug:
                    msg += " (%r != %r)" % (user.username, username)
                    logging.debug(msg)
                raise PermissionDenied("Wrong user!")

            return view_function(request, *args, **kwargs)
        return _check_user
    return _inner


# monkey patch for round all floats in json response
#def float_repr(f):
#    # XXX: Is this really needed???
#    return "%.2f" % round(f, 2)
#json.encoder.FLOAT_REPR = float_repr


def json_dumps(data, **extra):
    data_string = json.dumps(data, sort_keys=True, separators=(',', ':'), **extra)
#    data_string = data_string.replace("/", "\\/") # XXX: Is this really needed???
    return data_string


def json_response(debug=False):
    """
    A view can return tuple, list or dict:
        tupe: (item, weave timestamp) - item would be serialized
        list/dict: the weave timestamp would be added.
        
    TODO: handle "X-If-Unmodified-Since" header
    """
    def renderer(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            response = function(request, *args, **kwargs)

            if isinstance(response, HttpResponse):
                return response

            if isinstance(response, tuple):
                data, weave_timestamp = response
            elif isinstance(response, (dict, list)):
                data = response
                weave_timestamp = timestamp()
            else:
                msg = (
                    "json_response info: %s has not return tuple, dict or list, has return: %r (%r)"
                ) % (function.__name__, type(data), function.func_code)
                raise AssertionError(msg)

            if settings.DEBUG and "debug" in request.GET:
                logging.debug("debug output for %r:" % function.__name__)
                content_type = "text/plain"

                if int(request.GET["debug"]) > 1:
                    def load_payload(item):
                        if "payload" in item:
                            raw_payload = item["payload"]
                            payload_dict = json.loads(raw_payload)
                            item["payload"] = payload_dict
                        return item

                    if isinstance(data, list):
                        data = [load_payload(item) for item in data]
                    else:
                        data = load_payload(data)

                response_string = json_dumps(data, indent=4)

            else:
                accept = request.META.get('HTTP_ACCEPT', 'application/json')
#                if accept == "application/whoisi":
#                    content_type = "application/whoisi"
#                    response_string = struct.pack('!I', data.id) + json.dumps(data)
                if accept == "application/newlines":
                    content_type = "application/newlines"
                    if isinstance(data, list):
                        output = []
                        for obj in data:
                            output.append(json_dumps(obj))
                        response_string = "\n".join(output) # FIXME: '\n' -> r'\u000a' ???
                    else:
                        response_string = json_dumps(data)
                else:
                    content_type = "application/json"
                    response_string = json_dumps(data)

            response = HttpResponse(response_string, content_type=content_type)

            # https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#X-Weave-Timestamp
#            response["X-Weave-Timestamp"] = "%.2f" % weave_timestamp
            response["X-Weave-Timestamp"] = weave_timestamp

            # https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#X-Weave-Alert
#            response["X-Weave-Alert"] = "render debug for %r:" % function.__name__

            return response
        return wrapper
    return renderer
