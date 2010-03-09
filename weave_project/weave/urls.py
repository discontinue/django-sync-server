# coding: utf-8

"""
    :copyleft: 2010 by the django-weave team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


from django.conf.urls.defaults import patterns, url

from weave import views


urlpatterns = patterns('',
    url(r'^(?P<version>.*?)/(?P<username>.*?)/storage/(?P<col_name>.*?)/(?P<wboid>.*?)$', views.storage),
    url(r'^(?P<version>.*?)/(?P<username>.*?)/storage/(?P<col_name>.*?)$', views.storage),

    url(r'^(?P<version>.*?)/(?P<username>.*?)/info/collections$',
        views.info_collections, name='info_collections'),

    url(r'^misc/(?P<version>.*?)/captcha_html$', views.captcha_html, name='captcha_html'),

    url(r'^user/(?P<version>.*?)/(?P<username>.*?)/node/weave$', views.sign_in, name='sign_in'),
    url(r'^user/(?P<version>.*?)/(?P<username>.*?)$', views.exist_user, name='exist_user'),

    url(r'^user/(?P<username>.*?)/(?P<lock_path>.*?)$', views.handle_lock, name='handle_lock'),

    url(r'^api/register/chpwd/$', views.chpwd, name='chpwd'),
    url(r'^api/register/check/(?P<username>.*?)$', views.register_check, name='register_check'),

    url(r'^', views.root_view, name='root_view'),
)
