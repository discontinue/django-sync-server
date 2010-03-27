'''
URL mapping.

Created on 15.03.2010

@license: GNU GPL v3 or above, see LICENSE for more details.
@copyright: 2010 see AUTHORS for more details.
@author: Jens Diemer
@author: FladischerMichael
'''

from django.conf.urls.defaults import patterns

from weave.views import sync, user, misc

urlpatterns = patterns('weave',
    (r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/storage/(?P<col_name>.*?)/(?P<wboid>.*?)$', sync.storage),
    (r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/storage/(?P<col_name>.*?)$', sync.storage),
    (r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/storage$', sync.storage),
    (r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/info/collections$', sync.info),
    (r'^misc/(?P<version>[\d\.]+?)/captcha_html$', misc.captcha),
    (r'^user/(?P<version>[\d\.]+?)/(?P<username>.*?)/node/weave$', user.node),
    (r'^user/(?P<version>[\d\.]+?)/(?P<username>.*?)/password$', user.password),
    (r'^user/(?P<version>[\d\.]+?)/(?P<username>.*?)$', user.exists),
    (r'^api/register/check/(?P<username>.*?)$', user.register_check),
)
