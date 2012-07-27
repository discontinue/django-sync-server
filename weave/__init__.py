# coding:utf-8

"""
    -Logger helper class
    -build version string
    
    @license: GNU GPL v3 or above, see LICENSE for more details.
    @copyleft: 2010-2012 by the django-sync-server team, see AUTHORS for more details.
"""


import logging
import os
import subprocess
import time
import warnings


__version__ = (0, 4, 2)
__api__ = (1, 1)


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


if __name__ == "__main__":
    print VERSION_STRING
