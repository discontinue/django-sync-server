# coding: utf-8

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


__version__ = (0, 0, 1, 'pre-alpha')

# for setuptools
# - Only use . as a separator
# - No spaces: (0, 1, 0, 'beta') -> "0.1.0beta"
# http://peak.telecommunity.com/DevCenter/setuptools#specifying-your-project-s-version
VERSION_STRING = "%s.%s.%s%s" % __version__



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
#        except pkg_resources.DistributionNotFound, err:
#            warnings.warn("Distribution not found: %s" % err)


requirements = (
    # http://code.google.com/p/django-tools/
    "django-tools >= 0.6.0beta",

    # http://code.google.com/p/django-reversion/
    "django-reversion >= 1.1.2",
)

check_require(requirements)
