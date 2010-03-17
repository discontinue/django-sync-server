# coding: utf-8

"""
    :copyleft: 2010 by the django-weave team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import time
import httplib
import logging
import datetime
import traceback
from xml.etree import cElementTree as ET
from decimal import Decimal

try:
    import json # New in Python v2.6
except ImportError:
    from django.utils import simplejson as json


from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, HttpResponse

# http://code.google.com/p/django-tools/
from django_tools.decorators import check_permissions, render_to

# django-weave own stuff
from weave_project.weave.models import Lock, Collection, Wbo
from weave_project.weave.forms import ChangePasswordForm
from weave_project.weave.utils import timestamp, datetime2epochtime, WeaveTimestamp
from weave_project.weave.decorators import json_response


# from http://hg.mozilla.org/labs/weave/file/tip/tools/scripts/weave_server.py#l189
ERR_UID_OR_EMAIL_AVAILABLE = "1"
ERR_WRONG_HTTP_METHOD = "-1"
ERR_MISSING_UID = "-2"
ERR_INVALID_UID = "-3"
ERR_UID_OR_EMAIL_IN_USE = "0"
ERR_EMAIL_IN_USE = "-5"
ERR_MISSING_PASSWORD = "-8"
ERR_MISSING_RECAPTCHA_CHALLENGE_FIELD = "-6"
ERR_MISSING_RECAPTCHA_RESPONSE_FIELD = "-7"
ERR_MISSING_NEW = "-11"
ERR_INCORRECT_PASSWORD = "-12"
ERR_ACCOUNT_CREATED_VERIFICATION_SENT = "2"
ERR_ACCOUNT_CREATED = "3"


logging.basicConfig(level=logging.DEBUG)
#logging.debug('This is a debug message')
#logging.info('This is an info message')
#logging.warning('This is a warning message')
#logging.error('This is an error message')
#logging.critical('This is a critical error message')




class WeaveResponse(HttpResponse):
    def __init__(self, content='', status=None, content_type=None, weave_timestamp=None):
        super(WeaveResponse, self).__init__(content=content, status=status, content_type=content_type)

        if weave_timestamp is None:
            weave_timestamp = timestamp()
#        self["X-Weave-Timestamp"] = "%.2f" % weave_timestamp
        self["X-Weave-Timestamp"] = weave_timestamp


class PlaintextResponse(WeaveResponse):
    """ plaintext response with a status code in the content """
    def __init__(self, content="", status=None, weave_timestamp=None):
        super(PlaintextResponse, self).__init__(
            content=content, status=status, content_type="text/plain", weave_timestamp=weave_timestamp
        )


def render_xml_response(template_name, context, status=httplib.OK, weave_timestamp=None):
    rendered = render_to_string(template_name, context)
    response = WeaveResponse(
        content=rendered, content_type="text/xml", status=status, weave_timestamp=weave_timestamp
    )
    return response



class RecordNotFoundResponse(WeaveResponse):
    status_code = 404
    def __init__(self, msg, content):
        HttpResponse.__init__(self)
        self["X-Weave-Alert"] = msg
        self._container = [content]


#@render_to('weave/root_view.html')
@json_response(debug=True)
def root_view(request):
    print " *** root_view! ***"
    return {}


def wbo_timestamp_reponse(queryset):
    wbos = queryset.values("wboid", "modified")

    newest = 0
    timestamps = {}
    for wbo in wbos:
        modified = wbo["modified"]
        if modified > newest:
            newest = modified
        timestamps[wbo["wboid"]] = modified
#        timestamps[wbo["wboid"]] = "%.2f" % modified
#        timestamps[wbo["wboid"]] = WeaveTimestamp(modified)

    return timestamps, newest


#@assert_username(debug=True)
#@check_permissions(superuser_only=False, permissions=(u'weave.add_collection', u'weave.add_wbo'))
@json_response(debug=True)
def info_collections(request, version, username):
    """
    return a list of all exsiting collections with the newest wbo timestamp
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#GET
    
    e.g.: {"clients":1268646032.25,"crypto":1268149025.85,"forms":1268149016.51,"history":...}
    """
    user = User.objects.get(username=username)

    collections = Collection.on_site.filter(user=user)

    response_dict = {}
    for collection in collections:
        queryset = Wbo.objects.filter(collection=collection)
        queryset = queryset.order_by("-modified")
        queryset = queryset.values_list("modified", flat=True)
        newest_timestamp = queryset[0]
        response_dict[collection.name] = newest_timestamp

    return response_dict



def limit_wbo_queryset(request, queryset):
    """
    TODO:
    predecessorid = fromform(form, "predecessorid")
    full = fromform(form, "full")
    """
    GET = request.GET

    ids = GET.get("ids", None)
    if ids is not None:
#        ids = [id.strip() for id in ids.split(",") if id.strip()] 
        ids = ids.split(",")
        logging.debug("limit wbo queryset with ids: %r" % ids)
        queryset = queryset.filter(wboid__in=ids)

    parentid = GET.get("parentid", None)
    if parentid is not None:
        queryset = queryset.filter(parentid=parentid)

    newer = GET.get("newer", None)
    if newer is not None: # Greater than or equal to newer modified timestamp
        newer = float(newer)
        queryset = queryset.filter(modified__gte=newer)

    older = GET.get("older", None)
    if older is not None: # Less than or equal to older modified timestamp
        older = float(older)
        queryset = queryset.filter(modified__lte=older)

    index_above = GET.get("index_above", None)
    if index_above is not None: # Greater than or equal to index_above modified timestamp
        index_above = int(index_above)
        queryset = queryset.filter(sortindex__gte=index_above)

    index_below = GET.get("index_below", None)
    if index_below is not None: # Less than or equal to index_below modified timestamp
        index_below = int(index_below)
        queryset = queryset.filter(sortindex__lte=index_below)

    sort_type = GET.get("sort", None)
    if sort_type is not None:
        if sort_type == 'oldest':
            queryset = queryset.order_by("modified")
        elif sort_type == 'newest':
            queryset = queryset.order_by("-modified")
        elif sort_type == 'index':
            queryset = queryset.order_by("wboid")
        else:
            raise NameError("sort type %r unknown" % sort_type)

    offset = GET.get("offset", None)
    if offset is not None:
        offset = int(offset)
        queryset = queryset[offset:]

    limit = GET.get("limit", None)
    if limit is not None:
        limit = int(limit)
        queryset = queryset[:limit]

    return queryset



#@assert_username(debug=True)
#@check_permissions(superuser_only=False, permissions=(u'weave.add_collection', u'weave.add_wbo'))
@csrf_exempt
@json_response(debug=True)
def storage(request, version, username, col_name, wboid=None):
    """ Get/add/remove items from weave storage. """

#    user = request.user
    user = User.objects.get(username=username)

    if request.method == 'GET':
        # Returns a list of the WBO contained in a collection.
        try:
            collection = Collection.on_site.get(user=user, name=col_name)
        except Collection.DoesNotExist:
            msg = "Collection %r for user %r not found" % (col_name, username)
            logging.info(msg)
            if "full" in request.GET:
                return []
            else:
                return RecordNotFoundResponse(msg, content="")
        logging.debug("get collection %r" % collection)

        wbo_queryset = Wbo.objects.all().filter(user=user).filter(collection=collection)

        if wboid is not None: # return one WBO
            logging.debug("Use wboid %r to filter the queryset" % wboid)
            wbo_queryset = wbo_queryset.filter(wboid=wboid)
            qs_count = wbo_queryset.count()
            if qs_count == 0:
                msg = "wbo %r not found in collection %r" % (wboid, col_name)
                logging.debug(msg)
                return RecordNotFoundResponse(msg, content="")
            elif qs_count == 1:
                wbo = wbo_queryset[0]
                logging.debug("return only one WBO: %r" % wbo)
                response_dict = wbo.get_response_dict()
                return response_dict, wbo.modified
            logging.debug("more than one wbo found: queryset count: %r" % qs_count)
        else:
            wbo_queryset = limit_wbo_queryset(request, wbo_queryset)

            # If defined, returns the full WBO, rather than just the id. 
            full = request.GET.get("full", None)
            if full is None:
                logging.debug("GET parameter 'full' not set -> return only the WBO ids")
                return wbo_timestamp_reponse(wbo_queryset)

        newest_timestamp = 0
        wbo_list = []
        for wbo in wbo_queryset:
            if wbo.modified > newest_timestamp:
                newest_timestamp = wbo.modified
            response_dict = wbo.get_response_dict()
            wbo_list.append(response_dict)
        logging.info("Return a wbo list with %d items." % len(wbo_list))
        return wbo_list, newest_timestamp

    elif request.method in ("POST", "PUT"):
        # https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#PUT
        # Adds the WBO defined in the request body to the collection.
        raw_payload = request.raw_post_data
        if not raw_payload:
            # If the WBO does not contain a payload, it will only update
            # the provided metadata fields on an already defined object.
            raise NotImplemented

        collection = Collection.on_site.get_or_create2(user, col_name)

        payload = json.loads(raw_payload)

        if isinstance(payload, list):
            if request.method == "PUT":
                logging.error("PUT request with a payload array???")

            newest_timestamp = 0
            success_list = []
            for item in payload:
                # TODO: Check "invalid parentid", but how?
                wbo, created = Wbo.objects.create_or_update(item, collection, user)
                success_list.append(wbo.wboid)
                if wbo.modified > newest_timestamp:
                    newest_timestamp = wbo.modified

            # Returns a hash of successful and unsuccessful saves, including guidance as to possible errors: 
            # {"modified":1233702554.25,
            #   "success":["{GXS58IDC}12","{GXS58IDC}13","{GXS58IDC}15","{GXS58IDC}16","{GXS58IDC}18","{GXS58IDC}19"],
            #   "failed":{"{GXS58IDC}11":["invalid parentid"],"{GXS58IDC}14":["invalid parentid"],"{GXS58IDC}17":["invalid parentid"],"{GXS58IDC}20":["invalid parentid"]}
            # }
            response_dict = {"modified": newest_timestamp, "success":success_list, "failed":{}}
            return response_dict, newest_timestamp
        else:
            if request.method == "POST":
                logging.error("POST request without a payload array???")

            assert payload["id"] == wboid, "wrong wbo id: %r != %r" % (payload["id"], wboid)
            wbo, created = Wbo.objects.create_or_update(payload, collection, user)

            # return the timestamp associated with the modification.
            response_dict = {wboid: wbo.modified}
            return response_dict, wbo.modified

    elif request.method == 'DELETE':
        # The DELETE method seems not to work in this way, it's documented:
        # https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#DELETE
        try:
            collection = Collection.on_site.get(user=user, name=col_name)
        except Collection.DoesNotExist:
            logging.info("%r is not a collection key, try to delete a wbo" % col_name)
            wboid = col_name
        else:
            logging.info("Delete %r and all wbos in this collection for user %r" % (col_name, username))
            wbo_queryset = Wbo.objects.filter(user=user).filter(collection=collection)
            wbo_queryset = limit_wbo_queryset(request, wbo_queryset)
            logging.info("Delete wbo: %r" % wbo_queryset)
            wbo_queryset.delete()
            logging.info("Delete Collection: %r" % collection)
            collection.delete()
            return WeaveResponse()

        try:
            wbo = Wbo.objects.filter(user=user).get(wboid=wboid)
        except Wbo.DoesNotExist:
            msg = "Wbo %r not exist in collection %r for user %r" % (wboid, col_name, username)
            logging.info(msg)
            return RecordNotFoundResponse(msg, content="")
        logging.info("Delete wbo %r in collection %r for user %r" % (wboid, col_name, username))
        wbo.delete()
        return WeaveResponse()

    else:
        raise NotImplementedError("request.method %r not implemented!" % request.method)




def handle_lock(request, username, lock_path=None):
    """
    Is this really used by Firefox weave plugin?!?!
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print "User %r doesn't exist!" % username
        return PlaintextResponse(ERR_INVALID_UID)

    print "request.raw_post_data: %r" % request.raw_post_data

    if request.method == 'PROPFIND':
        if not lock_path:
            locks = Lock.objects.filter(user=user)
            items = [{"path": lock.lock_path, "prop": ""} for lock in locks]
            context = {"items": items}
            return render_xml_response("weave/propfind.xml", context, status=httplib.MULTI_STATUS)
        else:
            try:
                lock = Lock.objects.get(user=user, lock_path=lock_path)
            except Lock.DoesNotExist:
    #            count = Lock.objects.filter(user=user).count()
    #            token = "opaquelocktoken:%d" % (count + 1)
                context = {
                    "items": [{"path": lock_path, "prop": ""}]
                }
                return render_xml_response("weave/propfind.xml", context, status=httplib.MULTI_STATUS)

            context = {"token_id": lock.id}
            return render_xml_response("weave/lock.xml", context)
    elif request.method == 'LOCK':
        lock, created = Lock.objects.get_or_create(user=user, lock_path=lock_path)
        if created:
            lock.save()
            context = {"token_id": lock.id}
            return render_xml_response("weave/lock.xml", context)
        else:
            return HttpResponse(status=httplib.LOCKED)

#        raw_post_data = request.raw_post_data
#        elementtree = ET.XML(raw_post_data)
#        print elementtree
#        token = elementtree.find(".//{DAV:}locktoken/{DAV:}href").text
#        print token
#        print "XXX"
#        context = {"token_id": None}
#        return render_xml_response("weave/lock.xml", context)



    elif request.method == 'UNLOCK':
        token = request.META["HTTP_LOCK_TOKEN"]
        print "***", token

        try:
            lock = Lock.objects.get(user=user, lock_path=lock_path)
        except Lock.DoesNotExist:
            print "lock %r doesn't exist for user %r" % (lock_path, user)
            #return WeaveResponse(status=httplib.BAD_REQUEST)
        else:
            lock.delete()

        return WeaveResponse(status=httplib.NO_CONTENT)

    raise

#    def _handle_UNLOCK(self, path):
#        
#        if path not in self.locks:
#            return HttpResponse(httplib.BAD_REQUEST)
#        if token == "<%s>" % self.locks[path]:
#            del self.locks[path]
#            return HttpResponse(httplib.NO_CONTENT)
#        return HttpResponse(httplib.BAD_REQUEST)


    raise

#        return PlaintextResponse(status=httplib.LOCKED)


@csrf_exempt
def chpwd(request):
    """
    Change the user password.
    """
    if request.method != 'POST':
        logging.error("wrong request method %r" % request.method)
        return HttpResponseBadRequest()

    form = ChangePasswordForm(request.POST)
    if not form.is_valid():
        # TODO
        print "*** Form error:"
        print form.errors
        ERR_MISSING_UID
        ERR_MISSING_PASSWORD
        raise #FIXME return HttpResponseBadRequest(status=)

    username = form.cleaned_data["uid"]
    password = form.cleaned_data["password"] # the old password
    new = form.cleaned_data["new"] # the new password

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        logging.debug("User %r doesn't exist!" % username)
        return PlaintextResponse(ERR_INVALID_UID)

    if user.check_password(password) != True:
        logging.debug("Old password %r is wrong!" % password)
        return PlaintextResponse(ERR_INCORRECT_PASSWORD, httplib.BAD_REQUEST)
    else:
        logging.debug("Old password %r is ok." % password)

    user.set_password(new)
    user.save()
    logging.debug("Password for User %r changed from %r to %r" % (username, password, new))
    return PlaintextResponse()



def sign_in(request, version, username):
    """
    finding cluster for user -> return 404 -> Using serverURL as data cluster (multi-cluster support disabled)
    """
    assert version == "1"

    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        logging.debug("User %r doesn't exist!" % username)
        return PlaintextResponse(ERR_UID_OR_EMAIL_AVAILABLE)
    else:
        logging.debug("User %r exist." % username)

        return PlaintextResponse(ERR_UID_OR_EMAIL_IN_USE, status="404")


@csrf_exempt
def register_check(request, username):
    """
    Returns 1 if the username exist, 0 if not exist.
    """
    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        logging.debug("User %r doesn't exist!" % username)
        return PlaintextResponse(ERR_UID_OR_EMAIL_AVAILABLE)
    else:
        logging.debug("User %r exist." % username)
        return PlaintextResponse(ERR_UID_OR_EMAIL_IN_USE)



@csrf_exempt
def exist_user(request, version, username):
    """
    https://wiki.mozilla.org/Labs/Weave/User/1.0/API
    Returns 1 if the username is in use, 0 if it is available.
    
    e.g.: https://auth.services.mozilla.com/user/1/UserName
    """
    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        logging.debug("User %r doesn't exist!" % username)
        return PlaintextResponse("0")
    else:
        logging.debug("User %r exist." % username)
        return PlaintextResponse("1")


def captcha_html(request, version):
    print "_" * 79
    print "captcha_html:"
#    raise Http404
    #response = HttpResponse("11", status=400, content_type='application/json')
    response = HttpResponse("not supported")
    response["X-Weave-Timestamp"] = timestamp()
    return response


@json_response(debug=True)
def setup_user(request, version, username):
    absolute_uri = request.build_absolute_uri()
    return {}, timestamp()

