# coding:utf-8

"""
    -Logger helper class
    -build version string
    
    @license: GNU GPL v3 or above, see LICENSE for more details.
    @copyleft: 2010-2011 by the django-sync-server team, see AUTHORS for more details.
"""


import logging
import os
import subprocess
import time
import warnings


__version__ = (0, 2, 1)
__api__ = (1, 0)


VERSION_STRING = '.'.join(str(part) for part in __version__)
API_STRING = '.'.join(str(integer) for integer in __api__)


# Display get_git_hash() errors as warnings?
#VERBOSE = True
VERBOSE = False


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



def _error(msg):
    if VERBOSE:
        warnings.warn(msg)
    return ""

def get_commit_timestamp(path=None):
    if path is None:
        path = os.path.abspath(os.path.dirname(__file__))

    try:
        process = subprocess.Popen(
            # %ct: committer date, UNIX timestamp  
            ["/usr/bin/git", "log", "--pretty=format:%ct", "-1", "HEAD"],
            shell=False, cwd=path,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except Exception, err:
        return _error("Can't get git hash: %s" % err)

    process.wait()
    returncode = process.returncode
    if returncode != 0:
        return _error(
            "Can't get git hash, returncode was: %r"
            " - git stdout: %r"
            " - git stderr: %r"
            % (returncode, process.stdout.readline(), process.stderr.readline())
        )

    output = process.stdout.readline().strip()
    try:
        timestamp = int(output)
    except Exception, err:
        return _error("git log output is not a number, output was: %r" % output)

    try:
        return time.strftime(".%m%d", time.gmtime(timestamp))
    except Exception, err:
        return _error("can't convert %r to time string: %s" % (timestamp, err))


VERSION_STRING += get_commit_timestamp()


if __name__ == "__main__":
    print VERSION_STRING
