#coding:utf-8

"""
    django-weave unittests
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyleft: 2010 by the django-weave team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


if __name__ == "__main__":
    # run unittest directly
    # this works only in a created test virtualenv, see:
    # http://code.google.com/p/django-weave/wiki/CreateTestEnvironment
    import os
    os.environ["DJANGO_SETTINGS_MODULE"] = "testproject.settings"
    virtualenv_file = os.path.abspath("../../../bin/activate_this.py")
    execfile(virtualenv_file, dict(__file__=virtualenv_file))


from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test import TestCase


class SimpleTest(TestCase):
    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def test_register_check_user_not_exist(self):
        url = reverse("weave-register_check", kwargs={"username":"user doesn't exist"})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "1")

    def test_register_check_user_exist(self):
        User(username="testuser").save() # create a new user

        url = reverse("weave-register_check", kwargs={"username":"testuser"})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "0")


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
