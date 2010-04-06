# coding:utf-8


import os
import logging


__version__ = (0, 1, 5)
__api__ = (1, 0)


try:
    from django.utils.version import get_svn_revision
except ImportError:
    pass
else:
    path = os.path.split(os.path.abspath(__file__))[0]
    svn_revision = get_svn_revision(path)
    if svn_revision != u'SVN-unknown':
        svn_revision = svn_revision.replace("-", "").lower()
        __version__ += (svn_revision,)


VERSION_STRING = '.'.join(str(part) for part in __version__)
API_STRING = '.'.join(str(integer) for integer in __api__)


class Logging(object):
    """ 
    A private class that loads and caches some global objects.
    """
    logger = None

    def get_logger(cls):
        """ 
        Initializes and returns our logger instance.
        """
        if cls.logger is None:
            class NullHandler(logging.Handler):
                def emit(self, record):
                    pass

            cls.logger = logging.getLogger('django_weave')
            cls.logger.addHandler(NullHandler())
            cls.logger.setLevel(logging.DEBUG)

        return cls.logger
    get_logger = classmethod(get_logger)
