'''
Configuration.
Taken from http://pypi.python.org/pypi/django-auth-ldap/

Created on 19.03.2010

@license: GNU GPL v3 or above, see LICENSE for more details.
@copyright: 2010 see AUTHORS for more details.
@author: Michael Fladischer
'''

import logging

class _WeaveConfig(object):
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
