"""
    Simple script to test Weave server support and ensure that it
    works properly.
"""

import sys
import urllib
import urllib2
import httplib
from urlparse import urlsplit
from xml.etree import cElementTree as ET

import json
import weave_server
import threading

class DavRequest(urllib2.Request):
    def __init__(self, method, *args, **kwargs):
        urllib2.Request.__init__(self, *args, **kwargs)
        self.__method = method

    def get_method(self):
        return self.__method

class DavHandler(urllib2.BaseHandler):
    def _normal_response(self, req, fp, code, msg, headers):
        return fp

    # Multi-status
    http_error_207 = _normal_response

    # Created
    http_error_201 = _normal_response

    # Accepted
    http_error_202 = _normal_response

    # No content
    http_error_204 = _normal_response

class WeaveSession(object):
    def __init__(self, username, password, server_url,
                 realm=weave_server.DEFAULT_REALM):
        self.username = username
        self.server_url = server_url
        self.server = urlsplit(server_url).netloc
        self.realm = realm
        self.password = password

    def clone(self):
        return WeaveSession(self.username, self.password,
                            self.server_url, self.realm)

    def _open(self, req):
        davHandler = DavHandler()
        authHandler = urllib2.HTTPBasicAuthHandler()
        authHandler.add_password(self.realm,
                                 self.server,
                                 self.username,
                                 self.password)
        opener = urllib2.build_opener(authHandler, davHandler)
        if isinstance(req, urllib2.Request):
            print req.get_data()
            print req.get_full_url()
        else:
            print req
        return opener.open(req)

    def _get_user_url(self, path, user=None):
        if not user:
            user = self.username
        if path.startswith("/"):
            path = path[1:]
        url = "%s/user/%s/%s" % (self.server_url,
                                 user,
                                 path)
        return url

    def list_files(self, path):
        xml_data = ("<?xml version=\"1.0\" encoding=\"utf-8\" ?>"
                    "<D:propfind xmlns:D='DAV:'><D:prop/></D:propfind>")

        url = self._get_user_url(path)
        headers = {"Content-type" : "text/xml; charset=\"utf-8\"",
                   "Depth" : "1"}
        req = DavRequest("PROPFIND", url, xml_data, headers=headers)
        result_xml = self._open(req).read()

        multistatus = ET.XML(result_xml)
        hrefs = multistatus.findall(".//{DAV:}href")
        root = hrefs[0].text
        return [href.text[len(root):] for href in hrefs[1:]]

    def create_dir(self, path):
        req = DavRequest("MKCOL", self._get_user_url(path))
        self._open(req)

    def remove_dir(self, path):
        if not path[-1] == "/":
            path += "/"
        self.delete_file(path)

    def get_file(self, path, user=None):
        obj = self._open(self._get_user_url(path, user))
        return obj.read()

    def put_file(self, path, data):
        req = DavRequest("PUT", self._get_user_url(path), data)
        self._open(req)

    def delete_file(self, path):
        req = DavRequest("DELETE", self._get_user_url(path))
        self._open(req)

    def lock_file(self, path):
        headers = {"Content-type" : "text/xml; charset=\"utf-8\"",
                   "Depth" : "infinity",
                   "Timeout": "Second-600"}
        xml_data = ("<?xml version=\"1.0\" encoding=\"utf-8\" ?>\n"
                    "<D:lockinfo xmlns:D=\"DAV:\">\n"
                    "  <D:locktype><D:write/></D:locktype>\n"
                    "  <D:lockscope><D:exclusive/></D:lockscope>\n"
                    "</D:lockinfo>")
        req = DavRequest("LOCK", self._get_user_url(path), xml_data,
                         headers=headers)
        result_xml = self._open(req).read()

        response = ET.XML(result_xml)
        token = response.find(".//{DAV:}locktoken/{DAV:}href").text
        return token

    def unlock_file(self, path, token):
        headers = {"Lock-Token" : "<%s>" % token}
        req = DavRequest("UNLOCK", self._get_user_url(path),
                         headers=headers)
        self._open(req)

    def ensure_unlock_file(self, path):
        xml_data = ("<?xml version=\"1.0\" encoding=\"utf-8\" ?>"
                    "<D:propfind xmlns:D='DAV:'>"
                    "<D:prop><D:lockdiscovery/></D:prop></D:propfind>")

        url = self._get_user_url(path)
        headers = {"Content-type" : "text/xml; charset=\"utf-8\"",
                   "Depth" : "0"}
        req = DavRequest("PROPFIND", url, xml_data, headers=headers)
        try:
            result_xml = self._open(req).read()
        except urllib2.HTTPError, e:
            return

        multistatus = ET.XML(result_xml)
        href = multistatus.find(".//{DAV:}locktoken/{DAV:}href")
        if href is not None:
            self.unlock_file(path, href.text)

    def does_email_exist(self, email):
        return self._does_entity_exist("chkmail", email)

    def does_username_exist(self, username):
        return self._does_entity_exist("check", username)

    def _does_entity_exist(self, entity_kind, entity):
        url = "%s/api/register/%s/%s" % (self.server_url,
                                         entity_kind,
                                         entity)
        result = int(self._open(url).read())
        print "result: %r" % result
        if result == 0:
            return True
        elif result == 1:
            return False
        else:
            raise Exception("Unexpected result code: %d" % result)

    def change_password(self, new_password):
        url = "%s/api/register/chpwd/" % (self.server_url)
        postdata = urllib.urlencode({"uid" : self.username,
                                     "password" : self.password,
                                     "new" : new_password})
        req = urllib2.Request(url, postdata)
        print "change password reponse: %r" % self._open(req).read()
        self.password = new_password

    def share_with_users(self, path, users):
        url = "%s/api/share/" % (self.server_url)
        cmd = {"version" : 1,
               "directory" : path,
               "share_to_users" : users}
        postdata = urllib.urlencode({"cmd" : json.write(cmd),
                                     "uid" : self.username,
                                     "password" : self.password})
        req = urllib2.Request(url, postdata)
        result = self._open(req).read()
        if result != "OK":
            raise Exception("Share attempt failed: %s" % result)

def ensure_weave_disallows_php(session):
    print "Ensuring that weave disallows PHP upload and execution."
    session.put_file("phptest.php", "<?php echo 'hai2u!' ?>")
    try:
        if session.get_file("phptest.php") == "hai2u!":
            raise Exception("Weave server allows PHP execution!")
    finally:
        session.delete_file("phptest.php")

def _do_test(session_1, session_2):
    print "Ensuring that user '%s' exists." % session_1.username
    assert session_1.does_username_exist(session_1.username)

    print "Ensuring that user '%s' exists." % session_2.username
    assert session_1.does_username_exist(session_2.username)

    print "Changing password of user '%s' to 'blarg'." % session_1.username
    old_pwd = session_1.password
    old_session = session_1.clone()
    try:
        session_1.change_password("blarg")
    except urllib2.HTTPError, e:
        if (e.code == httplib.BAD_REQUEST and
            e.read() == weave_server.WeaveApp.ERR_INCORRECT_PASSWORD):
            print ("That didn't work; an old run of this test may "
                   "have been aborted.  Trying to revert...")
            session_1.password = "blarg"
            session_1.change_password(old_pwd)
            print "Revert successful, attempting to change password again."
            session_1.change_password("blarg")
        else:
            raise

    try:
        print "Ensuring we can't log in using old password."
        old_session.change_password("fnarg")
    except urllib2.HTTPError, e:
        if e.code != httplib.BAD_REQUEST:
            raise
        content = e.read()
        print "Content: %r" % content
        if content != weave_server.WeaveApp.ERR_INCORRECT_PASSWORD:
            raise AssertionError("Bad return value: %s" % content)
    else:
        raise AssertionError("We could log in using the old password!")

    print "Reverting back to old password."
    session_1.change_password(old_pwd)

    print
    print "*" * 79
    print

    print "Ensuring that file is not locked."
    session_1.ensure_unlock_file("test_lock")

    print "Locking file"
    session_1.lock_file("test_lock")

    print "Unlocking file by querying for its token"
    session_1.ensure_unlock_file("test_lock")

    print "Locking file again"
    token = session_1.lock_file("test_lock")

    try:
        print "Ensuring that we can't re-lock the file."
        session_1.lock_file("test_lock")
    except urllib2.HTTPError, e:
        if e.code != httplib.LOCKED:
            raise
    else:
        raise AssertionError("We can re-lock the file!")

    print "Unlocking file"
    session_1.unlock_file("test_lock", token)

    # FIXME
#    print "Ensuring that PROPFIND on the user's home dir works."
#    files = session_1.list_files("")

#    print "Cleaning up any files left over from a failed previous test."
#    if "blargle/bloop" in files:
#        session_1.delete_file("blargle/bloop")
#    if "blargle/" in files:
#        session_1.remove_dir("blargle")

    print "Creating directory."
    session_1.create_dir("blargle")

    print "Ensuring that directory indexes don't raise errors."
    session_1.get_file("")

    try:
        print "Creating temporary file."
        session_1.put_file("blargle/bloop", "hai2u!")
        print "Verifying that temporary file is listed."
        assert "bloop" in session_1.list_files("blargle/")
        try:
            assert session_1.get_file("blargle/bloop") == "hai2u!"
            session_1.share_with_users("blargle", [])
            try:
                print "Ensuring user 2 can't read user 1's file."
                session_2.get_file("blargle/bloop", session_1.username)
            except urllib2.HTTPError, e:
                if e.code != httplib.UNAUTHORIZED:
                    raise
            else:
                raise AssertionError("User 2 can read user 1's file!")
            print "Sharing directory with user 2."
            session_1.share_with_users("blargle", [session_2.username])
            print "Ensuring user 2 can read user 1's file."
            assert session_2.get_file("blargle/bloop",
                                      session_1.username) == "hai2u!"
            print "Sharing directory with everyone."
            session_1.share_with_users("blargle", ["all"])
            print "Ensuring user 2 can read user 1's file."
            assert session_2.get_file("blargle/bloop",
                                      session_1.username) == "hai2u!"
        finally:
            session_1.delete_file("blargle/bloop")
    finally:
        print "Removing directory."
        session_1.remove_dir("blargle")

    ensure_weave_disallows_php(session_1)

    print "Test complete."

def redirect_stdio(func):
    def wrapper(*args, **kwargs):
        from cStringIO import StringIO
        old_stdio = [sys.stdout, sys.stderr]
        stream = StringIO()
        sys.stderr = sys.stdout = stream
        try:
            try:
                return func(*args, **kwargs)
            except Exception, e:
                import traceback
                traceback.print_exc()
                raise Exception("Test failed:\n\n%s" % stream.getvalue())
        finally:
            sys.stderr, sys.stdout = old_stdio

    wrapper.__name__ = func.__name__
    return wrapper

@redirect_stdio
def test_weave_server():
    server_url = "http://127.0.0.1:%d" % weave_server.DEFAULT_PORT
    username_1 = "foo"
    password_1 = "test123"
    username_2 = "bar"
    password_2 = "test1234"

    start_event = threading.Event()

    def run_server():
        app = weave_server.WeaveApp()
        app.add_user(username_1, password_1)
        app.add_user(username_2, password_2)
        httpd = weave_server.make_server('', weave_server.DEFAULT_PORT, app)
        start_event.set()
        while 1:
            request, client_address = httpd.socket.accept()
            httpd.process_request(request, client_address)

    thread = threading.Thread(target=run_server)
    thread.setDaemon(True)
    thread.start()

    start_event.wait()

    session_1 = WeaveSession(username_1, password_1, server_url)
    session_2 = WeaveSession(username_2, password_2, server_url)

    _do_test(session_1, session_2)

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 5:
        print ("usage: %s <server-url> <username-1> <password-1> "
               "<username-2> <password-2>" % sys.argv[0])
        sys.exit(1)

    server_url = args[0]
    username_1 = args[1]
    password_1 = args[2]
    username_2 = args[3]
    password_2 = args[4]
    session_1 = WeaveSession(username_1, password_1, server_url)
    session_2 = WeaveSession(username_2, password_2, server_url)

    _do_test(session_1, session_2)
