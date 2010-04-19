
=============
 description
=============

django-weave is a reusable application which implements a Mozilla Labs Weave server for Django.

--------------
What is weave?
--------------

Weave Browser Sync is a free browser add-on from Mozilla Labs that keeps your
bookmarks, saved passwords, browsing history and open tabs backed up and
synchronized, with end-to-end encryption for your privacy and security.  

---------- 
sourcecode
----------

Our code hosted on github:
`http://github.com/jedie/django-weave`_

Clone our git repo::

    git clone git@github.com:jedie/django-weave.git

Use subversion::
  
    svn checkout http://svn.github.com/jedie/django-weave.git


--------
homepage
--------

:homepage:
  http://github.com/jedie/django-weave 

:old homepage:
  http://code.google.com/p/django-weave/
 

=========
 history
=========

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

Weave homepage:
`https://wiki.mozilla.org/Labs/Weave`_

more links here:
`http://code.google.com/p/django-weave/wiki/WeaveLinks`_
