'''
Utility functions for Weave API.

Created on 15.03.2010

@license: GNU GPL v3 or above, see LICENSE for more details.
@copyright: 2010 see AUTHORS for more details.
@author: Jens Diemer
@author: FladischerMichael
'''

import time
from datetime import datetime
    
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
        