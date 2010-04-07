'''
URL mapping.

Created on 15.03.2010

@license: GNU GPL v3 or above, see LICENSE for more details.
@copyright: 2010 see AUTHORS for more details.
@author: Jens Diemer
@author: FladischerMichael
'''

from django.conf.urls.defaults import patterns, url

from weave.views import sync, user, misc

urlpatterns = patterns('weave',
    url(r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/storage/(?P<col_name>.*?)/(?P<wboid>.*?)$', sync.storage),
    url(r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/storage/(?P<col_name>.*?)$', sync.storage),
    url(r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/storage$', sync.storage),
    url(r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/info/collections$', sync.info, name="weave-info"),
    url(r'^misc/(?P<version>[\d\.]+?)/captcha_html$', misc.captcha, name="weave-captcha"),
    url(r'^user/(?P<version>[\d\.]+?)/(?P<username>.*?)/node/weave$', user.node, name="weave-node"),
    url(r'^user/(?P<version>[\d\.]+?)/(?P<username>.*?)/password$', user.password, name="weave-password"),
    url(r'^user/(?P<version>[\d\.]+?)/(?P<username>.*?)$', user.exists, name="weave-exists"),
    url(r'^api/register/check/(?P<username>.*?)$', user.register_check, name="weave-register_check"),
)
