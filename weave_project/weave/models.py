# coding:utf-8

"""
    :copyleft: 2010 by the django-weave team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import logging
try:
    import json # New in Python v2.6
except ImportError:
    from django.utils import simplejson as json

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from django.contrib.sites.managers import CurrentSiteManager

# http://code.google.com/p/django-tools/
from django_tools.middlewares import ThreadLocal

# django-weave own stuff
from utils import timestamp, datetime2epochtime


logging.basicConfig(level=logging.DEBUG)


class BaseModel(models.Model):
    createtime = models.DateTimeField(auto_now_add=True, help_text="Create time")
    lastupdatetime = models.DateTimeField(auto_now=True, help_text="Time of the last change.")

    createby = models.ForeignKey(User, editable=False, related_name="%(class)s_createby",
        null=True, blank=True, # <- If the model used outsite a real request (e.g. unittest, db shell)
        help_text="User how create this entry.")
    lastupdateby = models.ForeignKey(User, editable=False, related_name="%(class)s_lastupdateby",
        null=True, blank=True, # <- If the model used outsite a real request (e.g. unittest, db shell)
        help_text="User as last edit this entry.")

    def save(self, *args, **kwargs):
        """
        Automatic update createby and lastupdateby attributes with the request object witch must be
        the first argument.
        """
        current_user = ThreadLocal.get_current_user()

        if current_user and isinstance(current_user, User):
            if self.pk == None or kwargs.get("force_insert", False): # New model entry
                self.createby = current_user
            self.lastupdateby = current_user

        return super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Lock(BaseModel):
    user = models.ForeignKey(User)
    lock_path = models.CharField(max_length=255)
#    lock_type = models.CharField(max_length=255)
#    lock_scope = models.CharField(max_length=255)
#    depth = models.CharField(max_length=255)
#    timeout = models.PositiveIntegerField()

    class Meta:
        unique_together = ("user", "lock_path")



class CollectionManager(CurrentSiteManager):
    def get_or_create2(self, user, col_name):
        collection, created = self.get_or_create(
            user=user, name=col_name
        )
        if created:
            logging.info("Collection %r created" % collection)
            current_site = Site.objects.get_current()
            collection.sites.add(current_site)
            collection.save()
        else:
            logging.info("Collection %r exists" % collection)

        return collection


class Collection(BaseModel):
    """
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/Setup
    
    inherited from BaseModel:
        createtime     -> datetime of creation
        lastupdatetime -> datetime of the last change
        createby       -> ForeignKey to user who creaded this entry
        lastupdateby   -> ForeignKey to user who has edited this entry
    """
    user = models.ForeignKey(User)
    name = models.CharField(max_length=96)

    sites = models.ManyToManyField(Site, default=[settings.SITE_ID])
    on_site = CollectionManager('sites')

    def site_info(self):
        """ for admin.ModelAdmin list_display """
        sites = self.sites.all()
        return ", ".join([site.name for site in sites])
    site_info.short_description = _('Exists on site')
    site_info.allow_tags = False

    def __unicode__(self):
        return u"%r (user %r)" % (self.name, self.user.username)

    class Meta:
        ordering = ("-lastupdatetime",)


class WboManager(models.Manager):
    def create_or_update(self, payload_dict, collection, user):
        """
        create or update a wbo
        TODO:
            - Check parentid, but how?
            - must wboid + parentid be unique?
        """
        wbo, created = Wbo.objects.get_or_create(
            collection=collection, user=user, wboid=payload_dict["id"],
            defaults={
                "parentid": payload_dict.get("parentid", None),
                "predecessorid": payload_dict.get("predecessorid", None),
                "sortindex": payload_dict.get("sortindex", None),
                "modified": payload_dict.get("modified", timestamp()),
                "payload": payload_dict["payload"],
            }
        )
        if created:
            msg = "New wbo %r created" % wbo.wboid
        else:
            wbo.parentid = payload_dict.get("parentid", None)
            wbo.predecessorid = payload_dict.get("predecessorid", None)
            wbo.sortindex = payload_dict.get("sortindex", None)
            wbo.modified = payload_dict.get("modified", timestamp())
            wbo.payload = payload_dict["payload"]
            wbo.save()
            msg = "Existing wbo %r updated" % wbo.wboid

        logging.info("%s (collection: %r, user: %r)" % (msg, collection.name, user.username))
        return wbo, created



class Wbo(BaseModel):
    """
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API   
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/Setup
    
    inherited from BaseModel:
        createtime     -> datetime of creation
        lastupdatetime -> datetime of the last change
        createby       -> ForeignKey to user who creaded this entry
        lastupdateby   -> ForeignKey to user who has edited this entry
    """
    objects = WboManager()

    collection = models.ForeignKey(Collection, blank=True, null=True)
    user = models.ForeignKey(User)
    wboid = models.CharField(max_length=64, blank=True,
        help_text="wbo identifying string"
    )
    parentid = models.CharField(max_length=64, blank=True, null=True,
        help_text="wbo parent identifying string"
    )
    predecessorid = models.CharField(max_length=64, blank=True, null=True,
        help_text="wbo predecessorid"
    )
    sortindex = models.IntegerField(null=True, blank=True,
        help_text="An integer indicting the relative importance of this item in the collection.",
    )
    modified = models.FloatField(help_text="X-Weave-Timestamp")
    payload = models.TextField(blank=True,
        help_text=(
            "A string containing a JSON structure encapsulating the data of the record."
            " This structure is defined separately for each WBO type. Parts of the"
            " structure may be encrypted, in which case the structure should also"
            " specify a record for decryption."
        )
    )
    def get_response_dict(self):
        response_dict = {
            "id": self.wboid,
            "modified": self.modified,
            "payload": self.payload,
        }
        for key in ("parentid", "predecessorid", "sortindex"):
            value = getattr(self, key)
            if value:
                response_dict[key] = value
        return response_dict

    def __unicode__(self):
        return u"%r (%r)" % (self.wboid, self.collection)

    class Meta:
        ordering = ("-lastupdatetime",)
