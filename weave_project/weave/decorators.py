# coding: utf-8

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
        print "Error: json (or simplejson) module is needed"
        sys.exit(1)

from django.http import HttpResponse

# django-weave own stuff
from utils import timestamp, datetime2epochtime


def assert_username(debug=False):
    """ Check if the username from the url is logged in. """
    def _inner(view_function):
        @wraps(view_function)
        def _check_user(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated():
                msg = "Permission denied for anonymous user. Please log in."
                if debug:
                    print msg
                raise PermissionDenied(msg)

            username = kwargs["username"]
            if user.username != username:
                msg = "Wrong user!"
                if debug:
                    msg += " (%r != %r)" % (user.username, username)
                    print msg
                raise PermissionDenied("Wrong user!")

            return view_function(request, *args, **kwargs)
        return _check_user
    return _inner



def json_response(debug=False):
    """ return a dict as a json string """
    def renderer(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            response = function(request, *args, **kwargs)

            if isinstance(response, HttpResponse):
                if debug:
                    print "render debug for %r:" % function.__name__
                    print "response: %r" % response
                    print "response.content:", response.content
                return response

            data, weave_timestamp = response

            if not isinstance(data, (dict, list)):
                msg = (
                    "json_response info: %s has not return a dict, has return: %r (%r)"
                ) % (function.__name__, type(data), function.func_code)
                raise AssertionError(msg)

            try:
                data_string = json.dumps(data)
            except Exception, err:
                print traceback.format_exc()
                raise

            content_type = 'text/plain'
#            content_type = 'application/json'

            response = HttpResponse(data_string, content_type=content_type)
            # https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#X-Weave-Timestamp

            response["X-Weave-Timestamp"] = "%.2f" % weave_timestamp
#            response["X-Weave-Timestamp"] = weave_timestamp

            # https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#X-Weave-Alert
#            response["X-Weave-Alert"] = "render debug for %r:" % function.__name__

            if debug:
                print "render debug for %r:" % function.__name__
                print "data: %r" % data
                print "response.content:", response.content

            return response
        return wrapper
    return renderer
