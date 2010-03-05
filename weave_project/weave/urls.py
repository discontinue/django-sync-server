# coding: utf-8

"""
    :copyleft: 2010 by the django-weave team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


from django.conf.urls.defaults import patterns, url

from weave import views


urlpatterns = patterns('',
#    url(r'^/tags/(?P<tag>.*?)/$', tag_view, name='Blog-tag_view'),
#    url(r'^/(?P<id>.*?)/(?P<title>.*?)/$', detail_view, name='Blog-detail_view'),

    #/1.0/user2/storage/meta/global
    #/1.0/user2/storage/crypto/bookmarks
    #/1.0/user2/storage/bookmarks
    #/1.0/user2/storage/crypto/forms
    #/1.0/user2/storage/crypto/history
    #/1.0/user2/storage/crypto/passwords
    #/1.0/user2/storage/crypto/prefs
    #/1.0/user2/storage/crypto/tabs
    #/1.0/user2/storage/tabs


    url(r'^/(?P<version>.*?)/(?P<username>.*?)/storage/(?P<col_name>.*?)/(?P<wboid>.*?)$', views.storage),
    url(r'^/(?P<version>.*?)/(?P<username>.*?)/storage/(?P<wboid>.*?)$', views.storage_wboid),

    #/1.0/UserName/info/collections
    url(r'^/(?P<version>.*?)/(?P<username>.*?)/info/collections$',
        views.info_collections, name='info_collections'),

    url(r'^/misc/(?P<version>.*?)/captcha_html$', views.captcha_html, name='captcha_html'),

    url(r'^/user/(?P<version>.*?)/(?P<username>.*?)/node/weave$', views.sign_in, name='sign_in'),
    url(r'^/user/(?P<version>.*?)/(?P<username>.*?)$', views.exist_user, name='exist_user'),

    url(r'^', views.root_view, name='root_view'),
)
