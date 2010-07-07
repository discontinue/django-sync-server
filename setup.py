#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    distutils setup
    ~~~~~~~~~~~~~~~

    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate$
    $Rev$
    $Author$

    :copyleft: 2010 by the django-sync-server team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import os
import sys

from setuptools import setup, find_packages

from weave import VERSION_STRING

PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))

def get_authors():
    authors = []
    f = file(os.path.join(PACKAGE_ROOT, "AUTHORS"), "r")
    for line in f:
        if line.startswith('*'):
            authors.append(line[1:].strip())
    f.close()
    return authors

def get_long_description():
    f = file(os.path.join(PACKAGE_ROOT, "README.rst"), "r")
    long_description = f.read()
    f.close()
    long_description.strip()
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
    include_package_data=True, # include package data under svn source control
    zip_safe=False,
    classifiers=[
#        "Development Status :: 1 - Planning",
#        "Development Status :: 2 - Pre-Alpha",
#        "Development Status :: 3 - Alpha",
        "Development Status :: 4 - Beta",
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
