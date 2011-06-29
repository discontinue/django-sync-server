#coding:utf-8

"""
    django-sync-server unittests
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyleft: 2010 by the django-sync-server team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import base64
import logging
import time


if __name__ == "__main__":
    # run unittest directly
    # this works only in a created test virtualenv, see:
    # http://code.google.com/p/django-sync-server/wiki/CreateTestEnvironment
    import os
    os.environ["DJANGO_SETTINGS_MODULE"] = "testproject.settings"


from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test import TestCase
from django.conf import settings

#from django_tools.utils import info_print
#info_print.redirect_stdout()

from weave.models import Wbo, Collection
from weave.views import sync
from weave import Logging
from weave.utils import make_sync_hash


def _enable_logging():
    logger = Logging.get_logger()
    handler = logging.StreamHandler()
    logger.addHandler(handler)


class WeaveServerTest(TestCase):
    def setUp(self, *args, **kwargs):
        super(WeaveServerTest, self).setUp(*args, **kwargs)

        settings.WEAVE.DISABLE_LOGIN = False

        # Create a test user with basic auth data
        self.testuser = User(username="testuser")
        raw_password = "test user password!"
        self.testuser.set_password(raw_password)
        self.testuser.save()

        raw_auth_data = "%s:%s" % (self.testuser.username, raw_password)
        self.auth_data = "basic %s" % base64.b64encode(raw_auth_data)

        self.client = Client()

    def tearDown(self, *args, **kwargs):
        super(WeaveServerTest, self).tearDown(*args, **kwargs)
        self.testuser.delete()

    def assertWeaveTimestamp(self, response):
        """ Check if a valid weave timestamp is in response. """
        key = "x-weave-timestamp"
        try:
            raw_timestamp = response[key]
        except KeyError, err:
            self.fail("Weave timestamp (%s) not in response." % key)

        timestamp = float(raw_timestamp)
        comparison_value = time.time() - 1
        self.failUnless(timestamp > comparison_value,
            "Weave timestamp %r is not bigger than comparison value %r" % (timestamp, comparison_value)
        )

    def test_register_check_user_not_exist(self):
        """ test user.register_check view with not existing user. """
        url = reverse("weave-register_check", kwargs={"username":"user doesn't exist"})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "1")

    def test_register_check_user_exist(self):
        """ test user.register_check view with existing test user. """
        url = reverse("weave-register_check", kwargs={"username":self.testuser.username})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "0")

    def test_exists_with_not_existing_user(self):
        """ test user.exists view with not existing user. """
        url = reverse("weave-exists", kwargs={"username":"user doesn't exist", "version":"1.0"})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "0")

    def test_exists_with_existing_user(self):
        """ test user.exists view with existing test user. """
        url = reverse("weave-exists", kwargs={"username":self.testuser.username, "version":"1.0"})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "1")

    def test_basicauth_get_authenticate(self):
        """ test if we get 401 'unauthorized' response. """
        url = reverse("weave-info", kwargs={"username":self.testuser.username, "version":"1.0"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 401) # Unauthorized: request requires user authentication
        self.failUnlessEqual(
            response["www-authenticate"], 'Basic realm="%s"' % settings.WEAVE.BASICAUTH_REALM
        )
        self.failUnlessEqual(response.content, "")

    def test_disable_basicauth(self):
        """ We should not get a basicauth response, if login is disabled. """
        settings.WEAVE.DISABLE_LOGIN = True
        url = reverse("weave-info", kwargs={"username":self.testuser.username, "version":"1.0"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 403) # Forbidden
        self.failIf("www-authenticate" in response)

    def test_basicauth_send_authenticate(self):
        """ test if we can login via basicauth. """
        url = reverse("weave-info", kwargs={"username":self.testuser.username, "version":"1.1"})
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_data)
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(response.content, "{}")
        self.failUnlessEqual(response["content-type"], "application/json")
        self.assertWeaveTimestamp(response)

    def test_create_wbo(self):
        url = reverse("weave-col_storage", kwargs={"username":"testuser", "version":"1.1", "col_name":"foobar"})
        data = (
            u'[{"id": "12345678-90AB-CDEF-1234-567890ABCDEF", "payload": "This is the payload"}]'
        )
        response = self.client.post(url, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.auth_data)
        self.failUnlessEqual(response.content, u'{"failed": [], "success": ["12345678-90AB-CDEF-1234-567890ABCDEF"]}')
        self.failUnlessEqual(response["content-type"], "application/json")

    def test_wbo_ttl_out_of_range1(self):
        self.assertRaises(
            ValidationError,
            Wbo.objects.create,
            user=self.testuser, wboid="1", payload="", payload_size=0, ttl= -1,
        )
    def test_wbo_ttl_out_of_range2(self):
        self.assertRaises(
            ValidationError,
            Wbo.objects.create,
            user=self.testuser, wboid="1", payload="", payload_size=0, ttl=31536001,
        )

    def test_post_wbo_ttl_out_of_range1(self):
        url = reverse(sync.storage, kwargs={"username":"testuser", "version":"1.1", "col_name":"foobar"})
        data = (
            u'[{"id": "1", "payload": "This is the payload", "ttl": -1}]'
        )
        response = self.client.post(url, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.auth_data)
        self.failUnlessEqual(response.content, u'{"failed": ["1"], "success": []}')
        self.failUnlessEqual(response["content-type"], "application/json")

    def test_post_wbo_ttl_out_of_range2(self):
        url = reverse(sync.storage, kwargs={"username":"testuser", "version":"1.1", "col_name":"foobar"})
#        settings.DEBUG = True
#        url += "?debug=1"
        data = (
            u'[{"id": "1", "payload": "This is the payload", "ttl": 31536001}]'
        )
        response = self.client.post(url, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.auth_data)
        self.failUnlessEqual(response.content, u'{"failed": ["1"], "success": []}')
        self.failUnlessEqual(response["content-type"], "application/json")

    def test_csrf_exempt(self):
        url = reverse("weave-col_storage", kwargs={"username":"testuser", "version":"1.1", "col_name":"foobar"})
        data = (
            u'[{"id": "12345678-90AB-CDEF-1234-567890ABCDEF", "payload": "This is the payload"}]'
        )
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(url, data=data, content_type="application/json", HTTP_AUTHORIZATION=self.auth_data)

        self.failUnlessEqual(response.content, u'{"failed": [], "success": ["12345678-90AB-CDEF-1234-567890ABCDEF"]}')
        self.failUnlessEqual(response["content-type"], "application/json")

        # Check if the csrf_exempt adds the csrf_exempt attribute to response:
        self.failUnlessEqual(response.csrf_exempt, True)

    def test_delete_not_existing_wbo(self):
        """
        http://github.com/jedie/django-sync-server/issues#issue/6
        """
        url = reverse("weave-wbo_storage",
            kwargs={
                "username":self.testuser.username, "version":"1.1",
                "col_name": "foobar", "wboid": "doesn't exist",
            }
        )
        response = self.client.delete(url, HTTP_AUTHORIZATION=self.auth_data)
        self.assertContains(response, "Page not found (404)", count=None, status_code=404)
        self.failUnlessEqual(response["content-type"], "text/html; charset=utf-8")

#        from django_tools.unittest_utils.BrowserDebug import debug_response
#        debug_response(response)

class WeaveServerUserTest(TestCase):
    def test_create_user(self):
#        _enable_logging()
        email = u"test@test.tld"
        sync_hash = make_sync_hash(email)
        url = reverse("weave-exists", kwargs={"username":sync_hash, "version":"1.0"})

        data = u'{"password": "12345678", "email": "%s", "captcha-challenge": null, "captcha-response": null}' % email

        # Bug in django? The post data doesn't transfered to view, if self.client.put() used
#        response = self.client.put(url, data=data, content_type="application/json")

        # But this works:
        response = self.client.post(url, data=data, content_type="application/json",
            REQUEST_METHOD="PUT"
            )

        self.failUnlessEqual(response.content, u"")

        # Check if user was created:
        user = User.objects.get(username=sync_hash)
        self.failUnlessEqual(user.email, email)


#__test__ = {"doctest": """
#Another way to test that 1 + 1 is equal to 2.
#
#>>> 1 + 1 == 2
#True
#"""}

if __name__ == "__main__":
    # Run all unittest directly
    from django.core import management

    tests = "weave"
#    tests = "weave.WeaveServerTest.test_create_user"
#    tests = "weave.WeaveServerTest.test_csrf_exempt"
#    tests = "weave.WeaveServerTest.test_post_wbo_ttl_out_of_range2"

    management.call_command('test', tests, verbosity=1)
