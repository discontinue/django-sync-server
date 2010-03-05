# coding:utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

# http://code.google.com/p/django-tools/
from django_tools.middlewares import ThreadLocal


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
    on_site = CurrentSiteManager('sites')

    def site_info(self):
        """ for admin.ModelAdmin list_display """
        sites = self.sites.all()
        return ", ".join([site.name for site in sites])
    site_info.short_description = _('Exists on site')
    site_info.allow_tags = False

    def __unicode__(self):
        return u"weave collection %r for user %r" % (self.name, self.user.username)

    class Meta:
        ordering = ("-lastupdatetime",)


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
    collection = models.ForeignKey(Collection, blank=True, null=True)
    user = models.ForeignKey(User)
    wboid = models.CharField(max_length=64, blank=True,
        help_text="wbo identifying string"
    )
    parentid = models.CharField(max_length=64, blank=True, null=True,
        help_text="wbo parent identifying string"
    )
    sortindex = models.IntegerField(null=True, blank=True,
        help_text="An integer indicting the relative importance of this item in the collection.",
    )
    payload = models.TextField(blank=True,
        help_text=(
            "A string containing a JSON structure encapsulating the data of the record."
            " This structure is defined separately for each WBO type. Parts of the"
            " structure may be encrypted, in which case the structure should also"
            " specify a record for decryption."
        )
    )

    def __unicode__(self):
        return u"weave wbo %r (%r)" % (self.wboid, self.collection)

    class Meta:
        ordering = ("-lastupdatetime",)
