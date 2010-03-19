
"""
    Check some external libs with pkg_resources.require()
    We only create warnings on VersionConflict and DistributionNotFound exceptions.
    
    See also: ./scripts/requirements/external_apps.txt
    See also: ./scripts/requirements/libs.txt
    
    Format info for pkg_resources.require():
    http://peak.telecommunity.com/DevCenter/PkgResources#requirement-objects
"""

import warnings
import pkg_resources

def check_require(requirements):
    """
    Check a package list.
    Display only warnings on VersionConflict and DistributionNotFound exceptions.
    """
    for requirement in requirements:
        try:
            pkg_resources.require(requirement)
        except pkg_resources.VersionConflict, err:
            warnings.warn("Version conflict: %s" % err)
        except pkg_resources.DistributionNotFound, err:
            warnings.warn("Distribution not found: %s" % err)


requirements = (
    # http://code.djangoproject.com/browser/django/trunk/django/__init__.py
    "django >= 1.2-beta-1",

    # http://code.google.com/p/django-tools/source/browse/trunk/django_tools/__init__.py
#    "django-tools >= 0.7.0beta",

    # http://code.google.com/p/django-reversion/source/browse/trunk/src/setup.py
#    "django-reversion >= 1.1.2",
)

check_require(requirements)
