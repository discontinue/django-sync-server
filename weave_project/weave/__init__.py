import logging

__version__ = (0, 1, 2)
__api__ = (1, 0)
VERSION_STRING = '.'.join(str(integer) for integer in __version__)
API_STRING = '.'.join(str(integer) for integer in __version__)


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
