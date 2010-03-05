"""
    weave_server.py [options]

    This is a simple reference implementation for a Weave server,
    which can also be used to test the Weave client against.

    This server behaves like a standard Weave server, with the
    following limitations and/or enhancements:

      * Responses to CAPTCHA challenges during new user registration
        are always accepted, with the exception that the magic word
        'bad' always fails (this was added for testing purposes).

      * Validation emails are not sent, though the server tells
        clients that they are.

      * The url at '/state/' can be accessed to retrieve a snapshot of
        the current state of the server.  This data can be saved to a
        file and restored later with the '--state' command-line
        option.  The state is also just a Pythonic representation of
        the server's state, and as such is relatively human-readable
        and can be hand-edited if necessary.

      * Timeout values sent with HTTP LOCK requests are ignored.

      * The server operates over HTTP, not HTTPS.
"""

from wsgiref.simple_server import make_server
from optparse import OptionParser
import httplib
import base64
import logging
import pprint
import cgi

DEFAULT_PORT = 8000
DEFAULT_REALM = "services.mozilla.com"
CAPTCHA_FAILURE_MAGIC_WORD = "bad"

class HttpResponse(object):
    def __init__(self, code, content = "", content_type = "text/plain"):
        self.status = "%s %s" % (code, httplib.responses.get(code, ""))
        self.headers = [("Content-type", content_type)]
        if code == httplib.UNAUTHORIZED:
            self.headers +=  [("WWW-Authenticate",
                               "Basic realm=\"%s\"" % DEFAULT_REALM)]
        if not content:
            content = self.status
        self.content = content

class HttpRequest(object):
    def __init__(self, environ):
        self.environ = environ
        content_length = environ.get("CONTENT_LENGTH")
        if content_length:
            stream = environ["wsgi.input"]
            self.contents = stream.read(int(content_length))
        else:
            self.contents = ""

class Perms(object):
    # Special identifier to indicate 'everyone' instead of a
    # particular user.
    EVERYONE = 0

    def __init__(self, readers=None, writers=None):
        if not readers:
            readers = []
        if not writers:
            writers = []

        self.readers = readers
        self.writers = writers

    def __is_privileged(self, user, access_list):
        return (user in access_list or self.EVERYONE in access_list)

    def can_read(self, user):
        return self.__is_privileged(user, self.readers)

    def can_write(self, user):
        return self.__is_privileged(user, self.writers)

    def __acl_repr(self, acl):
        items = []
        for item in acl:
            if item == self.EVERYONE:
                items.append("Perms.EVERYONE")
            else:
                items.append(repr(item))
        return "[" + ", ".join(items) + "]"

    def __repr__(self):
        return "Perms(readers=%s, writers=%s)" % (
            self.__acl_repr(self.readers),
            self.__acl_repr(self.writers)
            )

def requires_read_access(function):
    function._requires_read_access = True
    return function

def requires_write_access(function):
    function._requires_write_access = True
    return function

class WeaveApp(object):
    """
    WSGI app for the Weave server.
    """

    __CAPTCHA_HTML = '<html><head></head><body><script type=\'text/javascript\'>var RecaptchaOptions = {theme: \'red\', lang: \'en\'};</script><script type="text/javascript" src="http://api.recaptcha.net/challenge?k=6Lc_HwIAAAAAACneEwAadA-wKZCOrjo36TFQv160"></script>\n\n\t<noscript>\n  \t\t<iframe src="http://api.recaptcha.net/noscript?k=6Lc_HwIAAAAAACneEwAadA-wKZCOrjo36TFQv160" height="300" width="500" frameborder="0"></iframe><br/>\n  \t\t<textarea name="recaptcha_challenge_field" rows="3" cols="40"></textarea>\n  \t\t<input type="hidden" name="recaptcha_response_field" value="manual_challenge"/>\n\t</noscript></body></html>'

    def __init__(self, state=None):
        self.contents = {}
        self.dir_perms = {"/" : Perms(readers=[Perms.EVERYONE])}
        self.passwords = {}
        self.email = {}
        self.locks = {}
        self._tokenIds = 0

        if state:
            self.__setstate__(state)

    def add_user(self, username, password, email = None):
        assert username, "Username cannot be empty"
        assert password, "Password cannot be empty"

        home_dir = "/user/%s/" % username
        public_dir = home_dir + "public/"
        self.dir_perms[home_dir] = Perms(readers=[username],
                                         writers=[username])
        self.dir_perms[public_dir] = Perms(readers=[Perms.EVERYONE],
                                           writers=[username])
        self.passwords[username] = password
        if email:
            self.email[email] = username

    def __get_perms_for_path(self, path):
        possible_perms = [dirname for dirname in self.dir_perms
                          if path.startswith(dirname)]
        possible_perms.sort(key = len)
        perms = possible_perms[-1]
        return self.dir_perms[perms]

    def __get_files_in_dir(self, path):
        return [filename for filename in self.contents
                if filename.startswith(path)]

    def __api_share(self, path):
        params = cgi.parse_qs(self.request.contents)
        user = params["uid"][0]
        password = params["password"][0]
        if self.passwords.get(user) != password:
            return HttpResponse(httplib.UNAUTHORIZED)
        else:
            import json
            cmd = json.read(params["cmd"][0])
            dirname = "/user/%s/%s" % (user, cmd["directory"])
            if not dirname.endswith("/"):
                dirname += "/"
            readers = []
            for reader in cmd["share_to_users"]:
                if reader == "all":
                    readers.append(Perms.EVERYONE)
                else:
                    readers.append(reader)
            if user not in readers:
                readers.append(user)
            self.dir_perms[dirname] = Perms(readers = readers,
                                            writers = [user])
            return HttpResponse(httplib.OK, "OK")
    
    # Registration API
    def __api_register_check(self, what, where):
        what = what.strip("/")
        if what.strip() == "":
            return HttpResponse(400,
                                self.ERR_WRONG_HTTP_METHOD)
            
        if what in where:
            return HttpResponse(httplib.OK,
                                self.ERR_UID_OR_EMAIL_IN_USE)
        else:
            return HttpResponse(httplib.OK,
                                self.ERR_UID_OR_EMAIL_AVAILABLE)

    ERR_UID_OR_EMAIL_AVAILABLE = "1"
    ERR_WRONG_HTTP_METHOD = "-1"
    ERR_MISSING_UID = "-2"
    ERR_INVALID_UID = "-3"
    ERR_UID_OR_EMAIL_IN_USE = "0"
    ERR_EMAIL_IN_USE = "-5"
    ERR_MISSING_PASSWORD = "-8"
    ERR_MISSING_RECAPTCHA_CHALLENGE_FIELD = "-6"
    ERR_MISSING_RECAPTCHA_RESPONSE_FIELD = "-7"
    ERR_MISSING_NEW = "-11"
    ERR_INCORRECT_PASSWORD = "-12"
    ERR_ACCOUNT_CREATED_VERIFICATION_SENT = "2"
    ERR_ACCOUNT_CREATED = "3"

    __REQUIRED_CHANGE_PASSWORD_FIELDS = ["uid", "password", "new"]

    __REQUIRED_NEW_ACCOUNT_FIELDS = ["uid",
                                     "password",
                                     "recaptcha_challenge_field",
                                     "recaptcha_response_field"]

    __FIELD_ERRORS = {
        "uid" : ERR_MISSING_UID,
        "password" : ERR_MISSING_PASSWORD,
        "new" : ERR_MISSING_NEW,
        "recaptcha_challenge_field" : ERR_MISSING_RECAPTCHA_CHALLENGE_FIELD,
        "recaptcha_response_field" : ERR_MISSING_RECAPTCHA_RESPONSE_FIELD
        }

    def __get_fields(self, required_fields):
        params = cgi.parse_qs(self.request.contents)
        fields = {}
        for name in params:
            fields[name] = params[name][0]
        for name in required_fields:
            if not fields.get(name):
                return HttpResponse(httplib.BAD_REQUEST,
                                    self.__FIELD_ERRORS[name])
        return fields

    def __api_create_account(self, path):
        fields = self.__get_fields(self.__REQUIRED_NEW_ACCOUNT_FIELDS)
        if isinstance(fields, HttpResponse):
            return fields
        if fields["uid"] in self.passwords:
            return HttpResponse(httplib.BAD_REQUEST,
                                self.ERR_UID_OR_EMAIL_IN_USE)
        if fields["recaptcha_response_field"] == CAPTCHA_FAILURE_MAGIC_WORD:
            return HttpResponse(httplib.EXPECTATION_FAILED)
        if fields.get("mail"):
            if self.email.get(fields["mail"]):
                return HttpResponse(httplib.BAD_REQUEST,
                                    self.ERR_EMAIL_IN_USE)
            # TODO: We're not actually sending an email...
            body_code = self.ERR_ACCOUNT_CREATED_VERIFICATION_SENT
        else:
            body_code = self.ERR_ACCOUNT_CREATED

        self.add_user(fields["uid"], fields["password"],
                      fields.get("mail"))
        return HttpResponse(httplib.CREATED, body_code)

    def __api_change_password(self, path):
        fields = self.__get_fields(self.__REQUIRED_CHANGE_PASSWORD_FIELDS)
        if isinstance(fields, HttpResponse):
            return fields
        if not self.passwords.get(fields["uid"]):
            return HttpResponse(httplib.BAD_REQUEST,
                                self.ERR_INVALID_UID)
        if self.passwords[fields["uid"]] != fields["password"]:
            return HttpResponse(httplib.BAD_REQUEST,
                                self.ERR_INCORRECT_PASSWORD)
        self.passwords[fields["uid"]] = fields["new"]
        return HttpResponse(httplib.OK)

    # HTTP method handlers

    @requires_write_access
    def _handle_LOCK(self, path):
        if path in self.locks:
            return HttpResponse(httplib.LOCKED)
        token = "opaquelocktoken:%d" % self._tokenIds
        self._tokenIds += 1
        self.locks[path] = token
        response = """<?xml version="1.0" encoding="utf-8"?>
                   <D:prop xmlns:D="DAV:">
                     <D:lockdiscovery>
                       <D:activelock>
                         <D:locktoken>
                           <D:href>%s</D:href>
                         </D:locktoken>
                       </D:activelock>
                     </D:lockdiscovery>
                   </D:prop>""" % token
        return HttpResponse(httplib.OK, response, content_type="text/xml")

    @requires_write_access
    def _handle_UNLOCK(self, path):
        token = self.request.environ["HTTP_LOCK_TOKEN"]
        if path not in self.locks:
            return HttpResponse(httplib.BAD_REQUEST)
        if token == "<%s>" % self.locks[path]:
            del self.locks[path]
            return HttpResponse(httplib.NO_CONTENT)
        return HttpResponse(httplib.BAD_REQUEST)

    @requires_write_access
    def _handle_MKCOL(self, path):
        return HttpResponse(httplib.OK)

    @requires_write_access
    def _handle_PUT(self, path):
        self.contents[path] = self.request.contents
        return HttpResponse(httplib.OK)

    def _handle_POST(self, path):
        if path == "/api/share/":
            return self.__api_share(path)
        elif path == "/api/register/new/":
            return self.__api_create_account(path)
        elif path == "/api/register/chpwd/":
            return self.__api_change_password(path)
        else:
            return HttpResponse(httplib.NOT_FOUND)

    @requires_write_access
    def _handle_PROPFIND(self, path):
        response = """<?xml version="1.0" encoding="utf-8"?>
                   <D:multistatus xmlns:D="DAV:" xmlns:ns0="DAV:">"""

        path_template = """<D:response>
                           <D:href>%(href)s</D:href>
                           <D:propstat>
                           <D:prop>
                           %(props)s
                           </D:prop>
                           <D:status>HTTP/1.1 200 OK</D:status>
                           </D:propstat>
                           </D:response>"""

        if path in self.locks:
            props = "<D:locktoken><D:href>%s</D:href></D:locktoken>" % (
                self.locks[path]
                )
        else:
            props = ""

        response += path_template % {"href": path,
                                     "props": props}

        if path.endswith("/"):
            for filename in self.__get_files_in_dir(path):
                response += path_template % {"href" : filename,
                                             "props" : ""}

        response += """</D:multistatus>"""
        return HttpResponse(httplib.MULTI_STATUS, response,
                            content_type="text/xml")

    @requires_write_access
    def _handle_DELETE(self, path):
        response = HttpResponse(httplib.OK)
        if path.endswith("/"):
            # Delete a directory.
            for filename in self.__get_files_in_dir(path):
                del self.contents[filename]
        else:
            # Delete a file.
            if path not in self.contents:
                response = HttpResponse(httplib.NOT_FOUND)
            else:
                del self.contents[path]
        return response

    @requires_read_access
    def _handle_GET(self, path):
        if path in self.contents:
            return HttpResponse(httplib.OK, self.contents[path])
        elif path == "/state/":
            state_str = pprint.pformat(self.__getstate__())
            return HttpResponse(httplib.OK, state_str)
        elif path == "/api/register/new/":
            return HttpResponse(httplib.OK, self.__CAPTCHA_HTML,
                                content_type = "text/html")
        elif path.startswith("/api/register/check/"):
            return self.__api_register_check(path[20:], self.passwords)
        elif path.startswith("/api/register/chkmail/"):
            return self.__api_register_check(path[22:], self.email)
        elif path.endswith("/"):
            return self.__show_index(path)
        else:
            return HttpResponse(httplib.NOT_FOUND)

    def __getstate__(self):
        state = {}
        state.update(self.__dict__)
        del state["request"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __show_index(self, path):
        output = []
        for filename in self.__get_files_in_dir(path):
            output.append("<p><a href=\"%s\">%s</a></p>" % (filename,
                                                            filename))
        if output:
            output = "".join(output)
        else:
            output = ("<p>There are no files under the "
                      "directory <tt>%s</tt>.</p>" % (path))
        return HttpResponse(httplib.OK, output, content_type="text/html")

    def __process_handler(self, handler):
        response = None
        auth = self.request.environ.get("HTTP_AUTHORIZATION")
        if auth:
            user, password = base64.b64decode(auth.split()[1]).split(":")
            if self.passwords.get(user) != password:
                response = HttpResponse(httplib.UNAUTHORIZED)
        else:
            user = Perms.EVERYONE

        if response is None:
            path = self.request.environ["PATH_INFO"]
            perms = self.__get_perms_for_path(path)
            checks = []
            if hasattr(handler, "_requires_read_access"):
                checks.append(perms.can_read)
            if hasattr(handler, "_requires_write_access"):
                checks.append(perms.can_write)
            for check in checks:
                if not check(user):
                    response = HttpResponse(httplib.UNAUTHORIZED)

        if response is None:
            response = handler(path)

        return response

    def __call__(self, environ, start_response):
        """
        Main WSGI application method.
        """

        self.request = HttpRequest(environ)
        method = "_handle_%s" % environ["REQUEST_METHOD"]

        # See if we have a method called 'handle_<method>', where
        # <method> is the name of the HTTP method to call.  If we do,
        # then call it.
        if hasattr(self, method):
            handler = getattr(self, method)
            response = self.__process_handler(handler)
        else:
            response = HttpResponse(
                httplib.METHOD_NOT_ALLOWED,
                "Method %s is not yet implemented." % method
                )

        start_response(response.status, response.headers)
        return [response.content]

if __name__ == "__main__":
    usage = __import__("__main__").__doc__
    parser = OptionParser(usage = usage)
    parser.add_option("-s", "--state", dest="state_filename",
                      help="retrieve server state from filename")
    options, args = parser.parse_args()

    print "Weave Development Server"
    print
    print "Run this script with '-h' for usage information."

    logging.basicConfig(level=logging.DEBUG)

    if options.state_filename:
        filename = options.state_filename
        logging.info("Setting initial state from '%s'." % filename)
        data = open(filename, "r").read()
        state = eval(data)
        app = WeaveApp(state)
    else:
        app = WeaveApp()

    logging.info("Serving on port %d." % DEFAULT_PORT)
    httpd = make_server('', DEFAULT_PORT, app)
    httpd.serve_forever()
