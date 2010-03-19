'''
Register all weave models in Django admin interface.

Created on 15.03.2010

@license: GNU GPL v3 or above, see LICENSE for more details.
@copyright: 2010 see AUTHORS for more details.
@author: Jens Diemer
@author: Michael Fladischer <michael@fladi.at>
'''

from django.contrib import admin
from reversion.admin import VersionAdmin

from weave.models import Wbo, Collection

class WboAdminInline(admin.TabularInline):
    model = Wbo

class WboAdmin(VersionAdmin):
    def payload_cutout(self, obj):
        MAX = 100
        payload = obj.payload
        if len(payload) > MAX:
            payload = payload[:MAX] + "..."
        return payload
    payload_cutout.short_description = "Payload cutout"
    list_display = ['id', "user", "wboid", 'collection', "parentid", "modified", "sortindex", "payload_cutout"]
    list_filter = ['user', 'collection']
    date_hierarchy = 'modified'
    search_fields = ("wboid", "parentid", "sortindex", "payload")

admin.site.register(Wbo, WboAdmin)

class CollectionAdmin(VersionAdmin):
    list_display = ['id', 'name', 'user', 'modified', 'site_info']
    list_filter = ['user']
    date_hierarchy = 'modified'
    inlines = [WboAdminInline]

admin.site.register(Collection, CollectionAdmin)
