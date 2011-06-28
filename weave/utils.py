# coding:utf-8

'''
    Utility functions for Weave API.
    
    Created on 15.03.2010
    
    @license: GNU GPL v3 or above, see LICENSE for more details.
    @copyright: 2010-2011 see AUTHORS for more details.
    @author: Jens Diemer
    @author: FladischerMichael
'''

from datetime import datetime
import base64
import hashlib
import time

from weave import Logging

logger = Logging.get_logger()


def weave_timestamp(timedata=None):
    if timedata is None:
        timedata = datetime.now()
    return time.mktime(timedata.timetuple())


def limit_wbo_queryset(request, queryset):
    """
    TODO:
    predecessorid = fromform(form, "predecessorid")
    full = fromform(form, "full")
    """
    GET = request.GET

    ids = GET.get("ids", None)
    if ids is not None:
        ids = ids.split(",")
        queryset = queryset.filter(wboid__in=ids)

    parentid = GET.get("parentid", None)
    if parentid is not None:
        queryset = queryset.filter(parentid=parentid)

    newer = GET.get("newer", None)
    if newer is not None: # Greater than or equal to newer modified timestamp
        queryset = queryset.filter(modified__gte=datetime.fromtimestamp(float(newer)))

    older = GET.get("older", None)
    if older is not None: # Less than or equal to older modified timestamp
        queryset = queryset.filter(modified__lte=datetime.fromtimestamp(float(older)))

    index_above = GET.get("index_above", None)
    if index_above is not None: # Greater than or equal to index_above modified timestamp
        queryset = queryset.filter(sortindex__gte=int(index_above))

    index_below = GET.get("index_below", None)
    if index_below is not None: # Less than or equal to index_below modified timestamp
        queryset = queryset.filter(sortindex__lte=int(index_below))

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
        queryset = queryset[int(offset):]

    limit = GET.get("limit", None)
    if limit is not None:
        queryset = queryset[:int(limit)]

    return queryset


def make_sync_hash(txt):
    """
    make a base32 encoded SHA1 hash value.
    Used in firefox sync for creating a username from the email address.
    See also:
    https://hg.mozilla.org/services/minimal-server/file/5ee9d9a4570a/weave_minimal/create_user#l87
    """
    sha1 = hashlib.sha1(txt).digest()
    base32encode = base64.b32encode(sha1).lower()
    return base32encode
