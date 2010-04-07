# coding: utf-8

from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import weave.urls
from testproject.views import url_info


handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'


urlpatterns = patterns('',
    url(r'^$', url_info),
    url(r'^weave/', include(weave.urls), name="weave-root"),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
