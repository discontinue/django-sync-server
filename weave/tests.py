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


from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test import TestCase
from django.conf import settings

from weave import Logging

# Uncomment this, to see logging output:
#logger = Logging.get_logger()
#handler = logging.StreamHandler()
#logger.addHandler(handler)


class WeaveServerTest(TestCase):
    def _pre_setup(self, *args, **kwargs):
        super(WeaveServerTest, self)._pre_setup(*args, **kwargs)

        # Create a test user with basic auth data
        self.testuser = User(username="testuser")
        raw_password = "test user password!"
        self.testuser.set_password(raw_password)
        self.testuser.save()

        raw_auth_data = "%s:%s" % (self.testuser.username, raw_password)
        self.auth_data = "basic %s" % base64.b64encode(raw_auth_data)

    def _post_teardown(self, *args, **kwargs):
        super(WeaveServerTest, self)._post_teardown(*args, **kwargs)
        self.testuser.delete()

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

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
        url = reverse("weave-info", kwargs={"username":self.testuser.username, "version":"1.0"})
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_data)
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(response.content, "{}")
        self.failUnlessEqual(response["content-type"], "application/json")
        self.assertWeaveTimestamp(response)

    def test_delete_not_existing_wbo(self):
        """
        http://github.com/jedie/django-sync-server/issues#issue/6
        """
        url = reverse("weave-wbo_storage",
            kwargs={
                "username":self.testuser.username, "version":"1.0",
                "col_name": "foobar", "wboid": "doesn't exist",
            }
        )
        response = self.client.delete(url, HTTP_AUTHORIZATION=self.auth_data)
        self.assertContains(response, "Page not found (404)", count=None, status_code=404)
        self.failUnlessEqual(response["content-type"], "text/html; charset=utf-8")
        
#        from django_tools.unittest_utils.BrowserDebug import debug_response
#        debug_response(response)


#__test__ = {"doctest": """
#Another way to test that 1 + 1 is equal to 2.
#
#>>> 1 + 1 == 2
#True
#"""}

if __name__ == "__main__":
    # Run all unittest directly
    from django.core import management
    management.call_command('test', "weave", verbosity=1)
