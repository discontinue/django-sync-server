#!/usr/bin/env python
# coding: utf-8

"""
    distutils setup
    ~~~~~~~~~~~~~~~

    :copyleft: 2010-2011 by the django-sync-server team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import os
import sys

from setuptools import setup, find_packages

from weave import VERSION_STRING

PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_authors():
    authors = []
    try:
        f = file(os.path.join(PACKAGE_ROOT, "AUTHORS"), "r")
    except Exception, err:
        return ["[Error reading AUTHORS file: %s]" % err]
    for line in f:
        if line.startswith('*'):
            authors.append(line[1:].strip())
    f.close()
    return authors


def get_long_description():
    """
    returns README.creole as ReStructuredText.
    Code from:
        https://code.google.com/p/python-creole/wiki/UseInSetup
    """
    desc_creole = ""
    try:
        f = file(os.path.join(PACKAGE_ROOT, "README.creole"), "r")
        desc_creole = f.read()
        f.close()
        desc_creole = unicode(desc_creole, 'utf-8').strip()

        try:
            from creole import creole2html, html2rest
        except ImportError:
            etype, evalue, etb = sys.exc_info()
            evalue = etype("%s - Please install python-creole, e.g.: pip install python-creole" % evalue)
            raise etype, evalue, etb

        desc_html = creole2html(desc_creole)
        long_description = html2rest(desc_html)
    except Exception, err:
        if "sdist" in sys.argv or "--long-description" in sys.argv:
            raise
        # Don't raise the error e.g. in ./setup install process
        long_description = "[Error: %s]\n%s" % (err, desc_creole)

    return long_description


setup(
    name='django-sync-server',
    version=VERSION_STRING,
    description='django-sync-server is a Django reusable application witch implements a Firefox weave server.',
    long_description=get_long_description(),
    author=get_authors(),
    maintainer="Jens Diemer",
    maintainer_email="django-sync-server@jensdiemer.de",
    url='http://code.google.com/p/django-sync-server/',
    packages=find_packages(exclude=['testproject', 'testproject.*']),
    include_package_data=True, # include files specified by MANIFEST.in
    install_requires=[
        "Django>=1.3,<1.4", # Django v1.3.x
        "South",
    ],
    zip_safe=False,
    classifiers=[
#        "Development Status :: 1 - Planning",
#        "Development Status :: 2 - Pre-Alpha",
#        "Development Status :: 3 - Alpha",
#        "Development Status :: 4 - Beta",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
#        "Intended Audience :: Education",
#        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        'Framework :: Django',
        "Topic :: Database :: Front-Ends",
        "Topic :: Documentation",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Operating System :: OS Independent",
    ]
)
