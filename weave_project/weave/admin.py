# coding: utf-8

"""
    PyLucid.admin
    ~~~~~~~~~~~~~~

    Register all PyLucid model in django admin interface.

    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate$
    $Rev$
    $Author$

    :copyleft: 2010 by the django-weave team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.contrib.auth.admin import UserAdmin

from reversion.admin import VersionAdmin

from weave.models import Lock, Wbo, Collection

class LockAdmin(VersionAdmin):
    list_display = ("id", "lastupdatetime", "user", "lock_path")
    date_hierarchy = 'lastupdatetime'

admin.site.register(Lock, LockAdmin)


class WboAdmin(VersionAdmin):
    def payload_cutout(self, obj):
        MAX = 100
        payload = obj.payload
        if len(payload) > MAX:
            payload = payload[:MAX] + "..."
        return payload
    payload_cutout.short_description = "Payload cutout"
#    view_on_site_link.allow_tags = True

    list_display = ("id", "lastupdatetime", "modified", "user", "wboid", "parentid", "predecessorid", "sortindex", "lastupdateby", "payload_cutout")
    list_display_links = ("wboid",)
    list_filter = ("user", "collection", "predecessorid", "parentid")
    date_hierarchy = 'lastupdatetime'
    search_fields = ("wboid", "parentid", "predecessorid", "sortindex", "payload")

admin.site.register(Wbo, WboAdmin)


class CollectionAdmin(VersionAdmin):
    """
    """
    list_display = ("id", "lastupdatetime", "user", "name", "lastupdateby")
    list_display_links = ("name",)
    list_filter = ("user", "createby", "lastupdateby",)
    date_hierarchy = 'lastupdatetime'
#    search_fields = ("headline", "content")

admin.site.register(Collection, CollectionAdmin)


if settings.DEBUG:
    from reversion.models import Revision, Version

    class RevisionAdmin(admin.ModelAdmin):
        list_display = ("id", "date_created", "user", "comment")
        list_display_links = ("date_created",)
        date_hierarchy = 'date_created'
        ordering = ('-date_created',)
        list_filter = ("user", "comment")
        search_fields = ("user", "comment")

    admin.site.register(Revision, RevisionAdmin)


    class VersionAdmin(admin.ModelAdmin):
        list_display = ("object_repr", "revision", "object_id", "content_type", "format",)
        list_display_links = ("object_repr", "object_id")
        list_filter = ("content_type", "format")
        search_fields = ("object_repr", "serialized_data")

    admin.site.register(Version, VersionAdmin)


