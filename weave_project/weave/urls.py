'''
URL mapping.

Created on 15.03.2010

@license: GNU GPL v3 or above, see LICENSE for more details.
@copyright: 2010 see AUTHORS for more details.
@author: Jens Diemer
@author: FladischerMichael
'''

from django.conf.urls.defaults import patterns

urlpatterns = patterns('weave',
    (r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/storage/(?P<col_name>.*?)/(?P<wboid>.*?)$', 'views.sync.storage'),
    (r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/storage/(?P<col_name>.*?)$', 'views.sync.storage'),
    (r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/storage$', 'views.sync.storage'),
    (r'^(?P<version>[\d\.]+?)/(?P<username>.*?)/info/collections$', 'views.sync.info'),
    (r'^misc/(?P<version>[\d\.]+?)/captcha_html$', 'views.user.captcha_html'),
    (r'^user/(?P<version>[\d\.]+?)/(?P<username>.*?)/node/weave$', 'views.user.node'),
    (r'^user/(?P<version>[\d\.]+?)/(?P<username>.*?)$', 'views.user.exists'),
    (r'^api/register/chpwd/$', 'views.user.chpwd'),
    (r'^api/register/check/(?P<username>.*?)$', 'views.user.register_check'),
)
