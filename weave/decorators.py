# coding:utf-8

'''
    Decorators for view functions inside weave.
    HTTP basic auth decorators taken from:
    http://www.djangosnippets.org/snippets/243/

    Info:
    ~~~~~
    to debug the output in a browser: add "?debug=1" to a url.
    To reformat the payload: add "?debug=2" to a url.
    (This works only if settings.DEBUG==True)

    Created on 15.03.2010
    
    @license: GNU GPL v3 or above, see LICENSE for more details.
    @copyright: 2010 see AUTHORS for more details.
    @author: Jens Diemer
    @author: Scanner (http://www.djangosnippets.org/users/Scanner/)
    @author: Michael Fladischer <michael@fladi.at>
'''

from datetime import datetime
import base64
import pprint

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps # Python 2.3, 2.4 fallback.

try:
    import json # New in Python v2.6
except ImportError:
    from django.utils import simplejson as json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout

from weave.utils import weave_timestamp, make_sync_hash
from weave import Logging


logger = Logging.get_logger()


def view_or_basicauth(view, request, test_func, realm="", *args, **kwargs):
    """
    This is a helper function used by both 'logged_in_or_basicauth' and
    'has_perm_or_basicauth' that does the nitty of determining if they
    are already logged in or if they have provided proper http-authorization
    and returning the view if all goes well, otherwise responding with a 401.
    """
    if test_func(request.user):
        # Already logged in, just return the view.
        return view(request, *args, **kwargs)

    if settings.WEAVE.DISABLE_LOGIN:
        # disable weave own basicauth login, user must login before
        # using firefox-sync e.g. use the django admin login page.
        msg = "Request forbidden, basicauth was disabled."
        logger.debug(msg)
        if settings.DEBUG:
            return HttpResponseForbidden(msg)
        else:
            return HttpResponseForbidden()

    # They are not logged in. See if they provided login credentials
    if 'HTTP_AUTHORIZATION' in request.META:
        logger.debug("HTTP_AUTHORIZATION: %r" % request.META['HTTP_AUTHORIZATION'])
        # NOTE: We are only support basic authentication for now.
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) != 2:
            logger.debug("HTTP_AUTHORIZATION wrong length.")
            return HttpResponseBadRequest()

        auth_type, auth_data = auth

        if auth_type.lower() != "basic":
            logger.debug("HTTP_AUTHORIZATION is not 'basic'")
            return HttpResponseBadRequest()

        username, password = base64.b64decode(auth_data).split(':')

#        username = _fix_username(username)
#        if len(username) > 30:
#            logger.error("Username %r is longer than 30 characters!" % username)
#            return HttpResponseBadRequest()

        if len(password) > 256:
            logger.error("Password %r is longer than 256 characters!" % password)
            return HttpResponseBadRequest()

        user = authenticate(username=username, password=password)
        if user is None:
            logger.debug("basicauth error: user %r unknown or password wrong." % username)
        else:
            if not user.is_active:
                logger.debug("basicauth error: user %r is not active." % username)
            else:
                login(request, user)
                request.user = user
                logger.debug("basicauth success: user %r logged in." % username)
                return view(request, *args, **kwargs)

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    logger.debug("No HTTP_AUTHORIZATION send, yet.")
    response = HttpResponse()
    response.status_code = 401 # Unauthorized: request requires user authentication
    response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
    return response


def logged_in_or_basicauth(func, realm=settings.WEAVE.BASICAUTH_REALM):
    """
    A simple decorator that requires a user to be logged in. If they are not
    logged in the request is examined for a 'authorization' header.
    
    If the header is present it is tested for basic authentication and
    the user is logged in with the provided credentials.
    
    If the header is not present a http 401 is sent back to the
    requestor to provide credentials.
    
    The purpose of this is that in several django projects I have needed
    several specific views that need to support basic authentication, yet the
    web site as a whole used django's provided authentication.
    
    The uses for this are for urls that are access programmatically such as
    by rss feed readers, yet the view requires a user to be logged in. Many rss
    readers support supplying the authentication credentials via http basic
    auth (and they do NOT support a redirect to a form where they post a
    username/password.)
    
    Use is simple:
    
    @logged_in_or_basicauth
    def your_view:
        ...
    
    You can provide the name of the realm to ask for authentication within.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        return view_or_basicauth(func, request,
                                 lambda u: u.is_authenticated(),
                                 realm, *args, **kwargs)
    return wrapper


def has_perm_or_basicauth(func, perm, realm=""):
    """
    This is similar to the above decorator 'logged_in_or_basicauth'
    except that it requires the logged in user to have a specific
    permission.
    
    Use:
    
    @logged_in_or_basicauth('asforums.view_forumcollection')
    def your_view:
        ...
    
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        return view_or_basicauth(func, request,
                                 lambda u: u.has_perm(perm),
                                 realm, *args, **kwargs)
    return wrapper


def weave_assert_username(func, key='username'):
    """
    Decorator to check if the username from the URL is the one logged in.
    It uses the kwargs "username" as the default key but it can be changed by passing
    key='field' to the decorator. 
    
    Use:
    
    @weave_assert_username
    def your_view(request, username):
    
    You can provide the key of the username field which is 'username' by default.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Test if username argument matches logged in user.
        # Weave uses lowercase usernames inside the URL!!!

        url_username = kwargs[key].lower()
        logger.debug("Raw userdata from url: %r" % url_username)

        if request.user.username.lower() == url_username:
            # XXX obsolete weave 1.0 API ?
            logger.debug("Plaintext username %r from url is ok." % url_username)
            return func(request, *args, **kwargs)

        if not len(url_username) == 32:
            msg = "Wrong length of url userdata: %i" % len(url_username)
            logger.debug(msg + "(should be 32 characters long)")
            raise PermissionDenied(msg)

        # check new API
        email = request.user.email
        sync_hash = make_sync_hash(email)
        if url_username.startswith(sync_hash):
            logger.debug("Email hash %r from url is ok." % url_username)
            return func(request, *args, **kwargs)

        logger.debug("Url userdata %r doesn't fit to user %s" % (url_username, request.user.username))

        logger.info("Logout user %s" % request.user)
        logout(request)

        raise PermissionDenied("URL userdata doesn't fit to user from HTTP authentication.")

    return wrapper


def weave_assert_version(version):
    """
    Check the weave api version (comes from the url).
    
    Use:
    
    @weave_assert_version
    def your_view(request, username):
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not 'version' in kwargs:
                msg = "no version specified in URL"
                logger.error(msg)
                raise AssertionError(msg)

            url_version = kwargs['version']
            if isinstance(version, (list, tuple)) and url_version in version:
                return func(request, *args, **kwargs)
            elif url_version == version:
                return func(request, *args, **kwargs)

            msg = "unsupported weave client version: %r" % url_version
            logger.error(msg)
            raise AssertionError(msg)

        return wrapper
    return decorator


def weave_render_response(func):
    """
    Decorator that checks for the presence of weave specific HTTP headers 
    and formats output accordingly.
    
    Use:
    
    @weave_render_response
    def your_view(request):
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        timedata = datetime.now()
        data = func(request, timestamp=timedata, *args, **kwargs)
        logger.debug("Raw response data for %r: %r" % (func.__name__, data))
        response = HttpResponse()
        response["X-Weave-Timestamp"] = weave_timestamp(timedata)

        if settings.DEBUG and "debug" in request.GET:
            logger.debug("debug output for %r:" % func.__name__)

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

            response["content-type"] = "text/plain"
            response.content = json.dumps(data, indent=4)
        else:
            if request.META.get("HTTP_ACCEPT") == 'application/newlines' and isinstance(data, list):
                response.content = '\n'.join([json.dumps(element) for element in data]) + '\n'
                response["content-type"] = 'application/newlines'
                response['X-Weave-Records'] = len(data)
            else:
                response["content-type"] = "application/json"
                response.content = json.dumps(data)

        return response
    return wrapper


def debug_sync_request(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not settings.WEAVE.DEBUG_REQUEST:
            return func(request, *args, **kwargs)

        logger.debug("view args: %s" % repr(args))
        logger.debug("view kwargs: %s" % repr(kwargs))

        response = func(request, *args, **kwargs)

        logger.debug("request.GET: %s" % repr(request.GET))
        logger.debug("request.POST: %s" % pprint.pformat(request.POST))
        logger.debug("response.status_code: %r" % response.status_code)
        logger.debug("response headers: %s" % repr(response.items()))
        logger.debug("response raw content: %s" % repr(response.content))

        if response["content-type"] == "application/json":
            data = json.loads(response.content)
            logger.debug("content: %s" % json.dumps(data, indent=4))

        return response
    return wrapper


