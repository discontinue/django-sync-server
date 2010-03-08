# coding: utf-8

import os
import sys
import inspect
import traceback

from django.http import Http404
from django.conf import settings
from django.contrib.redirects.models import Redirect


MAX = 120
STACK_LIMIT = 6


def cut(s):
    s = repr(s)
    if len(s) > MAX:
        return s[:MAX] + "..."
    return s


def print_stack_info():
    """
    return stack_info: Where from the announcement comes?
    """
    self_basename = os.path.basename(__file__)
    if self_basename.endswith(".pyc"):
        # cut: ".pyc" -> ".py"
        self_basename = self_basename[:-1]

    stack_list = inspect.stack()
    # go forward in the stack, to outside of this file.
    for no, stack_line in enumerate(stack_list):
        filename = stack_line[1]
        if os.path.basename(filename) != self_basename:
            break

    stack_list = stack_list[no:no + STACK_LIMIT] # limit the displayed stack info

    stack_info = []
    for stack_line in reversed(stack_list):
        filename = cut(stack_line[1])
        lineno = stack_line[2]
        func_name = stack_line[3]
        print "%s %4s %s" % (filename, lineno, func_name)



class DebugMiddleware(object):
    def process_request(self, request):
        print "*** process_request():"
        print "request.path: %r" % request.path
        print "request.META['CONTENT_LENGTH']: %r" % request.META['CONTENT_LENGTH']
        print "request.GET: %r" % request.GET
        print "request.POST: %s" % cut(request.POST)
        print "request.FILES: %r" % request.FILES
        print "request.raw_post_data: %s" % cut(request.raw_post_data)
#        print_stack_info()
#        print sys.exc_info()

    def process_exception(self, request, exception):
        print "*** process_exception():"
#        print_stack_info()
        message = cut(str(exception))
        print message
        print traceback.format_exc()

    def process_response(self, request, response):
        print "*** process_response():"
#        print_stack_info()
#        print sys.exc_info()
        print "response: %r" % response
        print "response headers: %r" % response._headers
        print "response.status_code: %r" % response.status_code
        print "response.content: %s" % cut(response.content)
        return response
