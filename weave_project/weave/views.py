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

from weave.models import Lock, Collection, Wbo
from weave.forms import ChangePasswordForm
from weave.utils import timestamp, datetime2epochtime
from weave.decorators import json_response


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
    def __init__(self, *args, **kwargs):
        super(WeaveResponse, self).__init__(*args, **kwargs)
        self["X-Weave-Timestamp"] = timestamp()


class StatusResponse(WeaveResponse):
    """ plaintext response with a status code in the content """
    def __init__(self, content="", status=None):
        super(StatusResponse, self).__init__(
            content=content, mimetype=None, status=status, content_type="text/plain"
        )


def render_xml_response(template_name, context, status=httplib.OK):
    rendered = render_to_string(template_name, context)
    response = WeaveResponse(content=rendered, content_type="text/xml", status=status)
    return response



class RecordNotFoundResponse(HttpResponse):
    status_code = 404
    def __init__(self, content='"record not found"'):
        HttpResponse.__init__(self)
        self._container = [content]


#@render_to('weave/root_view.html')
@json_response(debug=True)
def root_view(request):
    print " *** root_view! ***"
    return



#@assert_username(debug=True)
#@check_permissions(superuser_only=False, permissions=(u'weave.add_collection', u'weave.add_wbo'))
@json_response(debug=True)
def info_collections(request, version, username):
    """
    return all collection keys with the timestamp
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#GET
    """
    user = User.objects.get(username=username)

    collection_qs = Collection.on_site.filter(user=user)
    queryset = Wbo.objects.all()
    queryset = queryset.filter(collection__in=collection_qs)
    wbos = queryset.values("wboid", "lastupdatetime")

    timestamps = {}
    for wbo in wbos:
        lastupdatetime = wbo["lastupdatetime"]
        timestamp = datetime2epochtime(lastupdatetime) # datetime -> time since the epoch
        timestamps[wbo["wboid"]] = str(timestamp)

    print timestamps
    return timestamps


#@assert_username(debug=True)
#@check_permissions(superuser_only=False, permissions=(u'weave.add_collection', u'weave.add_wbo'))
@csrf_exempt
@json_response(debug=True)
def storage_wboid(request, version, username, wboid):
    """
    get items from storage
    e.g.:
    GET /1.0/UserName/storage/history?newer=1265189444.85&full=1&sort=index&limit=1500
    """
    current_site = Site.objects.get_current()

#    user = request.user
    user = User.objects.get(username=username)

    if request.method == 'POST':
        payload = request.raw_post_data
        if not payload:
            # If the WBO does not contain a payload, it will only update
            # the provided metadata fields on an already defined object.
            raise NotImplemented

        collection, created = Collection.on_site.get_or_create(
            user=user, name=wboid
        )
        if created:
            logging.info("Collection %r created" % collection)
            collection.sites.add(current_site)
            collection.save()
        else:
            logging.info("Collection %r exists" % collection)

        data = json.loads(payload)
        if not isinstance(data, list):
            raise NotImplemented

        for item in data:
            wbo, created = Wbo.objects.get_or_create(
                collection=collection,
                user=user,
                wboid=item["id"],
                defaults={
                    "parentid": item.get("parentid", None), # FIXME: must wboid + parentid be unique?
                    "sortindex": item.get("sortindex", None),
                    "payload": item["payload"],
                }
            )
            if created:
                logging.info("New wbo created: %r" % wbo)
            else:
                wbo.parentid = item.get("parentid", None)
                wbo.sortindex = item.get("sortindex", None)
                wbo.payload = item["payload"]
                wbo.save()
                logging.info("Existing wbo updated: %r" % wbo)

#        assert val["id"] == wboid, "wrong wbo id: %r != %r" % (val["id"], wboid)
        return {}
    elif request.method == 'GET':
        try:
            wbo = Wbo.objects.filter(user=user).get(wboid=wboid)
        except Wbo.DoesNotExist:
            logging.info("Wbo %r not exist for user %r" % (wboid, user))
            return RecordNotFoundResponse()

        payload_dict = wbo.get_payload_dict()
        return payload_dict
    else:
        raise NotImplemented


#@assert_username(debug=True)
#@check_permissions(superuser_only=False, permissions=(u'weave.add_collection', u'weave.add_wbo'))
@csrf_exempt
@json_response(debug=True)
def storage(request, version, username, col_name, wboid):
    """

    """
    current_site = Site.objects.get_current()

#    user = request.user
    user = User.objects.get(username=username)

    if request.method == 'PUT':
        # https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#PUT
        # Adds the WBO defined in the request body to the collection.

        payload = request.raw_post_data
        if not payload:
            # If the WBO does not contain a payload, it will only update
            # the provided metadata fields on an already defined object.
            raise NotImplemented

        val = json.loads(payload)
        assert val["id"] == wboid, "wrong wbo id: %r != %r" % (val["id"], wboid)

        collection, created = Collection.on_site.get_or_create(
            user=user, name=col_name
        )
        if created:
            logging.info("Collection %r created" % collection)
            collection.sites.add(current_site)
            collection.save()
        else:
            logging.info("Collection %r exists" % collection)

        sortindex = val.get("sortindex", None)

        wbo = Wbo(
            collection=collection,
            user=user,
            wboid=wboid,
            sortindex=sortindex,
            payload=payload
        )
        wbo.save()

        # The server will return the timestamp associated with the modification.
        data = {wboid: datetime2epochtime(wbo.lastupdatetime)}
        return data
    elif request.method == 'GET':
        # Returns a list of the WBO ids contained in a collection.
        try:
            collection = Collection.on_site.get(user=user, name=col_name)
        except Collection.DoesNotExist:
            logging.info(
                "Collection %r for user %r not found" % (col_name, user)
            )
            return RecordNotFoundResponse()

        try:
            wbo = Wbo.objects.all().filter(collection=collection).get(wboid=wboid)
        except Wbo.DoesNotExist:
            logging.info(
                "Wbo %r not exist for collection %r" % (wboid, collection)
            )
            return RecordNotFoundResponse()

        payload_dict = wbo.get_payload_dict()
        return payload_dict
    else:
        raise NotImplemented




def handle_lock(request, username, lock_path=None):
    """
    Is this really used by Firefox weave plugin?!?!
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print "User %r doesn't exist!" % username
        return StatusResponse(ERR_INVALID_UID)

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

#        return StatusResponse(status=httplib.LOCKED)


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
        return StatusResponse(ERR_INVALID_UID)

    if user.check_password(password) != True:
        logging.debug("Old password %r is wrong!" % password)
        return StatusResponse(ERR_INCORRECT_PASSWORD, httplib.BAD_REQUEST)
    else:
        logging.debug("Old password %r is ok." % password)

    user.set_password(new)
    user.save()
    logging.debug("Password for User %r changed from %r to %r" % (username, password, new))
    return StatusResponse()



def sign_in(request, version, username):
    """
    finding cluster for user -> return 404 -> Using serverURL as data cluster (multi-cluster support disabled)
    """
    assert version == "1"

    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        logging.debug("User %r doesn't exist!" % username)
        return StatusResponse(ERR_UID_OR_EMAIL_AVAILABLE)
    else:
        logging.debug("User %r exist." % username)

        return StatusResponse(ERR_UID_OR_EMAIL_IN_USE, status="404")


@csrf_exempt
def register_check(request, username):
    """
    Returns 1 if the username exist, 0 if not exist.
    """
    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        logging.debug("User %r doesn't exist!" % username)
        return StatusResponse(ERR_UID_OR_EMAIL_AVAILABLE)
    else:
        logging.debug("User %r exist." % username)
        return StatusResponse(ERR_UID_OR_EMAIL_IN_USE)



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
        return StatusResponse("0")
    else:
        logging.debug("User %r exist." % username)
        return StatusResponse("1")


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
    return {}

