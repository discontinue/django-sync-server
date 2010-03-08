# coding: utf-8

import os
import sys
import inspect
import traceback

from django.http import Http404
from django.conf import settings
from django.utils import termcolors
from django.contrib.redirects.models import Redirect
from django.core.management.color import color_style

MAX = 120
STACK_LIMIT = 60


def cut(s):
    s = repr(s)
    if len(s) > MAX:
        return s[:MAX] + "..."
    return s


#def print_stack_info():
#    """
#    return stack_info: Where from the announcement comes?
#    """
#    self_basename = os.path.basename(__file__)
#    if self_basename.endswith(".pyc"):
#        # cut: ".pyc" -> ".py"
#        self_basename = self_basename[:-1]
#
#    stack_list = inspect.stack()
#    for stack_line in reversed(stack_list):
#        filename = cut(stack_line[1])
#        lineno = stack_line[2]
#        func_name = stack_line[3]
#        print "%s %4s %s" % (filename, lineno, func_name)
#
##    # go forward in the stack, to outside of this file.
##    for no, stack_line in enumerate(stack_list):
##        filename = stack_line[1]
##        if os.path.basename(filename) != self_basename:
##            break
##
##    stack_list = stack_list[no:no + STACK_LIMIT] # limit the displayed stack info
##
##    stack_info = []
##    for stack_line in reversed(stack_list):
##        filename = cut(stack_line[1])
##        lineno = stack_line[2]
##        func_name = stack_line[3]
##        print "%s %4s %s" % (filename, lineno, func_name)



class DebugMiddleware(object):
    style = color_style()

    def process_view(self, request, view_func, view_args, view_kwargs):
        print "*** DebugMiddleware.process_view():"
#        for i in dir(view_func):print i, getattr(view_func, i, "---")
        print "view: %s,  args: %r, kwagrs: %r" % (
            self.style.NOTICE(view_func.__name__), view_args, view_kwargs
        )

    def process_request(self, request):
        print "-" * 79
        print "*** DebugMiddleware.process_request():"
        print "request.path: %s" % self.style.SQL_FIELD(request.path)
        print "request.method: %r" % request.method
        print "request.META['CONTENT_LENGTH']: %r" % request.META['CONTENT_LENGTH']
#        for k, v in sorted(request.META.iteritems()): print k, v
        print "request.GET: %r" % request.GET
        print "request.POST: %s" % cut(request.POST)
        print "request.FILES: %r" % request.FILES
        print "request.raw_post_data: %s" % cut(request.raw_post_data)
#        print_stack_info()
#        print sys.exc_info()

    def process_exception(self, request, exception):
        print "*** DebugMiddleware.process_exception():"
#        print_stack_info()
        message = cut(str(exception))
        print message
        print traceback.format_exc()

    def process_response(self, request, response):
        print "*** DebugMiddleware.process_response():"
#        print_stack_info()
#        print sys.exc_info()
        print "response: %r" % response
        print "response headers: %r" % response._headers
        print "response.status_code: %r" % response.status_code
        print "response.content: %s" % cut(response.content)
#        print "response.content:"
#        print response.content
#        print "-" * 79
        with file("last_error_page.html", "w") as f:
            f.write(response.content)
        return response