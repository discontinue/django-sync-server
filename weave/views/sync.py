# coding: utf-8

'''
    Storage for Weave.
    
    Created on 15.03.2010
    
    @license: GNU GPL v3 or above, see LICENSE for more details.
    @copyleft: 2010 by the django-weave team, see AUTHORS for more details.
'''

from datetime import datetime

try:
    import json # New in Python v2.6
except ImportError:
    from django.utils import simplejson as json

from django.contrib.csrf.middleware import csrf_exempt
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

# django-weave own stuff
from weave.models import Collection, Wbo
from weave.utils import limit_wbo_queryset, weave_timestamp, assert_weave_version
from weave.decorators import weave_assert_username, logged_in_or_basicauth, \
  weave_render_response
from weave import Logging

logger = Logging.get_logger()

@logged_in_or_basicauth
@weave_assert_username
@csrf_exempt
@weave_render_response
def info(request, version, username, timestamp):
    """
    return all collection keys with the timestamp
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#GET
    """
    assert_weave_version(version)
    collections = dict()
    for collection in Collection.on_site.filter(user=request.user):
        collections[collection.name] = weave_timestamp(collection.modified)
    return collections


@logged_in_or_basicauth
@weave_assert_username
@csrf_exempt
@weave_render_response
def storage(request, version, username, timestamp, col_name=None, wboid=None):
    """
    Handle storing Collections and WBOs. 
    """
    assert_weave_version(version)
    if 'X-If-Unmodified-Since' in request.META:
        since = datetime.fromtimestamp(float(request.META['X-If-Unmodified-Since']))
    else:
        since = None

    if request.method == 'GET':
        # Returns a list of the WBO contained in a collection.
        collection = get_object_or_404(Collection.on_site, user=request.user, name=col_name)

        if wboid is not None: # return one WBO
            wbo = get_object_or_404(Wbo, user=request.user, collection=collection, wboid=wboid)
            return wbo.get_response_dict()

        wbo_queryset = Wbo.objects.filter(user=request.user, collection=collection)
        wbo_queryset = limit_wbo_queryset(request, wbo_queryset)

        # If defined, returns the full WBO, rather than just the id. 
        if not 'full' in request.GET: # return only the WBO ids
            return [wbo.wboid for wbo in wbo_queryset]

        return [wbo.get_response_dict() for wbo in wbo_queryset]

    elif request.method == 'PUT':
        # https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API#PUT
        # Adds the WBO defined in the request body to the collection.

        payload = request.raw_post_data
        logger.debug("Payload for PUT: %s" % payload)
        if not payload:
            raise NotImplementedError

        val = json.loads(payload)

        if val.get('id', None) != wboid:
            raise ValidationError

        # TODO: I don't think that it's good to just pass 0 in case the header is not defined
        collection, created = Collection.on_site.create_or_update(
                                                                  request.user,
                                                                  col_name,
                                                                  timestamp,
                                                                  since,
                                                                  )

        if created:
            logger.debug("Created new collection %s" % collection)
        else:
            logger.debug("Found existing collection %s" % collection)

        wbo, created = Wbo.objects.create_or_update(val, collection, request.user, timestamp)

        if created:
            logger.debug("New wbo created: %r" % wbo)
        else:
            logger.debug("Existing wbo updated: %r" % wbo)

        return weave_timestamp(timestamp)

    elif request.method == 'POST':
        status = {'success': [], 'failed': []}
        payload = request.raw_post_data
        logger.debug("Payload in POST: %s" % payload)
        if not payload:
            raise NotImplementedError

        # TODO: I don't think that it's good to just pass 0 in case the header is not defined
        collection, created = Collection.on_site.create_or_update(
                                                                  request.user,
                                                                  col_name,
                                                                  timestamp,
                                                                  since,
                                                                  )

        if created:
            logger.debug("Create new collection %s" % collection)
        else:
            logger.debug("Found existing collection %s" % collection)

        data = json.loads(payload)

        if not isinstance(data, list):
            raise NotImplementedError

        for item in data:
            wbo, created = Wbo.objects.create_or_update(item, collection, request.user, timestamp)
            status['success'].append(wbo.wboid)

            if created:
                logger.debug("New wbo created: %s" % wbo)
            else:
                logger.debug("Existing wbo updated: %s" % wbo)

        return status
    elif request.method == 'DELETE':
        # FIXME: This is am mess, it needs better structure
        if col_name is None and wboid is None:
            assert request.META.has_key('X-Confirm-Delete'), "To remove all records for your user, please make sure to include a X-Confirm-Delete HTTP header in your DELTE request!"
            Collection.on_site.filter(user=request.user).delete()
            return weave_timestamp(timestamp)

        if col_name is not None and wboid is not None:
            wbo = Wbo.objects.get(user=request.user, collection__name=col_name, wboid=wboid)
            if wbo is not None:
                logger.info("Delete Wbo %s in collection %s for user %s" % (wbo.wboid, col_name, request.user))
                wbo.delete()
            else:
                logger.info("Deletion of wboid %s requested but there is no such wbo!" % (wboid))
        else:
            ids = request.GET.get('ids', None)
            if ids is not None:
                for wbo in Wbo.objects.filter(user=request.user, wboid__in=ids.split(',')):
                    logger.info("Delete Wbo %s in collection %s for user %s" % (wbo.wboid, col_name, request.user))
                    wbo.delete()
            else:
                collection = Collection.on_site.filter(user=request.user, name=col_name).delete()
                if collection is not None:
                    logger.info("Delete collection %s for user %s" % (collection.name, request.user))
                    Wbo.objects.filter(user=request.user, collection=collection).delete()
                else:
                    logger.info("Deletion of collection %s requested but there is no such collection!" % (col_name))
        return weave_timestamp(timestamp)

    else:
        raise NotImplementedError("request.method %r not implemented!" % request.method)
