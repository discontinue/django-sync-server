=============
 description
=============

django-sync-server is a reusable application which implements a Firefox sync server for Django.

---------------------
What is Firefox Sync?
---------------------

Firefox Sync (formerly Mozilla Labs Weave Browser Sync) is a free browser
add-on from Mozilla Labs that keeps your bookmarks, saved passwords, browsing
history and open tabs backed up and synchronized, with end-to-end encryption
for your privacy and security.  

---------- 
sourcecode
----------

Our code hosted on `github.com/jedie/django-sync-server`_

.. _github.com/jedie/django-sync-server: http://github.com/jedie/django-sync-server

Clone our git repo::

    git clone git://github.com/jedie/django-sync-server.git

Use subversion::
  
    svn checkout http://svn.github.com/jedie/django-sync-server.git

--------
download
--------

Python packages available on: http://pypi.python.org/pypi/django-sync-server/

Unofficial debian packages: http://debian.fladi.at/pool/main/d/django-sync-server/


=========
 migrate
=========

- v0.3.0 to v0.4.0

We used django-south to change the existing models. Do this::

    ~$ cd django_sync_server_env
    ~/django_sync_server_env$ source bin/activate
    (django_sync_server_env)~/django_sync_server_env$ pip install South
    (django_sync_server_env)~/django_sync_server_env$ cd src/django-sync-server/testproject
    (django_sync_server_env)~/django_sync_server_env/src/django-sync-server/testproject$ ./manage.py syncdb
    (django_sync_server_env)~/django_sync_server_env/src/django-sync-server/testproject$ ./manage.py migrate weave 0001 --fake
    (django_sync_server_env)~/django_sync_server_env/src/django-sync-server/testproject$ ./manage.py migrate weave
 
Note: After South install, you must insert "south" in INSTALLED_APPS list in our own settings.py
see also: https://github.com/jedie/django-sync-server/commit/452668fb671662a15da2faf1e1c1f642d744b5dc#diff-1


=========
 history
=========

- v0.4.0

  - Updates to FxSync API 1.1 (see: https://github.com/jedie/django-sync-server/issues/11 )
  - Create a info page on root url

- v0.3.0

  - Add work-a-round for username longer than 30 characters (see: https://github.com/jedie/django-sync-server/issues/8 )
  - Add DONT_USE_CAPTCHA and DEBUG_REQUEST to app settings.

- v0.2.1

  - Some updates for django v1.2 API changes
  - Change version string and add last commit date

- v0.2.0

  - django-sync-server own basic auth function can be disabled via app settings.

- v0.1.7

  - 'django-weave' was renamed to 'django-sync-server'

- v0.1.6

  - Bugfix checking weave api version from url.
  - Add a tiny info root page to testproject.

- v0.1.5

  - Changes to establish compatibility with Weave client v1.2b3

- v0.1.4
  
  - split weave app and testproject

- v0.1.3

  - Remove dependency on django-reversion
  - change Collection sites ManyToManyField to a normal ForeignKey

- v0.1.2
  
  - many code cleanup and bugfixes
  - remove django-tools and django-reversion decencies

- v0.1.0pre-alpha

  - sync works

- v0.0.1

  - initial checkin

=============
 weave links
=============

Firefox Sync homepage: https://wiki.mozilla.org/Firefox_Sync

more links: http://code.google.com/p/django-sync-server/wiki/WeaveLinks
