# coding:utf-8

'''
    User handling for Weave.
    FIXME: Not complete yet.
    
    Created on 15.03.2010
    
    @license: GNU GPL v3 or above, see LICENSE for more details.
    @copyleft: 2010 by the django-weave team, see AUTHORS for more details.
'''

from django.contrib.auth.models import User
from django.contrib.csrf.middleware import csrf_exempt
from django.http import HttpResponseBadRequest, HttpResponse, \
    HttpResponseNotFound

# django-weave own stuff
from weave import constants
from weave.decorators import logged_in_or_basicauth
from weave import Logging

logger = Logging.get_logger()

@logged_in_or_basicauth
@csrf_exempt
def password(request):
    """
    Change the user password.
    """
    if request.method != 'POST':
        logger.error("wrong request method %r" % request.method)
        return HttpResponseBadRequest()
    
    # Make sure that we are able to change the password. 
    # If for example django-auth-ldap is used for authentication it will set the password for 
    # User objects to a unusable one in the database. Therefor we cannot change it, it has to 
    # happen inside LDAP.
    if request.user.has_usable_password():
        request.user.set_password(request.raw_post_data)
        request.user.save()
        logger.debug("Password for User %r changed to %r" % (request.user.username, request.raw_post_data))
        return HttpResponse()
    else:
        return HttpResponseBadRequest()

@csrf_exempt
def node(request, version, username):
    """
    finding cluster for user -> return 404 -> Using serverURL as data cluster (multi-cluster support disabled)
    """
    assert version == "1"

    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        logger.debug("User %r doesn't exist!" % username)
        return HttpResponseNotFound(constants.ERR_UID_OR_EMAIL_AVAILABLE)
    else:
        logger.debug("User %r exist." % username)
        #FIXME: Send the actual cluster URL instead of 404
        return HttpResponseNotFound(constants.ERR_UID_OR_EMAIL_IN_USE)


@csrf_exempt
def register_check(request, username):
    """
    Returns 1 if the username exist, 0 if not exist.
    """
    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        logger.debug("User %r doesn't exist!" % username)
        return HttpResponse(constants.ERR_UID_OR_EMAIL_AVAILABLE)
    else:
        logger.debug("User %r exist." % username)
        return HttpResponse(constants.ERR_UID_OR_EMAIL_IN_USE)


@csrf_exempt
def exists(request, version, username):
    """
    https://wiki.mozilla.org/Labs/Weave/User/1.0/API#GET
    Returns 1 if the username is in use, 0 if it is available.
    
    e.g.: https://auth.services.mozilla.com/user/1/UserName
    """
    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        logger.debug("User %r doesn't exist!" % username)
        return HttpResponse("0")
    else:
        logger.debug("User %r exist." % username)
        return HttpResponse("1")


@csrf_exempt
def captcha_html(request, version):
    """ TODO """
    logger.error("captcha is not implemented, yet.")
    raise NotImplemented()


