from distill import PY3


class Response(object):
    def __init__(self, status="200 OK", headers=None):
        """Initializes an empty response"""
        self.status = status
        if headers is None:
            headers = {}
        self.headers = headers
        self.body = None
        self.file = None
        self.file_len = None
        self.iterable = None

    @property
    def wsgi_headers(self):
        """Returns the response headers in the form WSGI expects"""
        if PY3:  # pragma: no cover
            items = list(self.headers.items())
        else:  # pragma: no cover
            items = self.headers.items()
        wsgilist = []
        for l in items:
            if type(l[1]) == list:
                wsgilist += [(l[0], li) for li in l[1]]
            else:
                wsgilist.append(l)
        return wsgilist

    def set_cookie(self, name, value, path="/", max_age=3600, domain=None,
                   secure=False, comment=None):
        """ Allows you to set a cookie on the client

         Notes:
            This function performs no check to ensure the cookie
            is not already set in the response.  Additionally, this
            function can be used to delete cookies by setting max_age
            to zero

        Args:
            name: The name of the cookie to set
            value: The value to give the cookie

        Kwargs:
            path: The path attribute on the cookie Default: /
            max_age: Time before the cookie expires Default: 3600
            domain: The domain attribute of the cookie Default: None
            secure: Is the cookie secure Default: False
            comment: The cookie comment Default: None
        """
        cookie = [(name, value), ("Max-Age", str(max_age)), ("Path", path), ("Version", "1")]

        if domain:
            if domain[:1] != '.':  # RFC specifies domains must start with a dot
                domain = '.{0}'.format(domain)
            cookie.append(("Domain", domain))
        if secure:
            cookie.append(("Secure", None))
        if comment:
            cookie.append(("Comment", comment))

        cookie = '; '.join([attr for attr in ["%s=%s" % (key, value) if value else key for (key, value) in cookie]])
        self.headers.setdefault('Set-Cookie', [])
        self.headers['Set-Cookie'].append(cookie)

    def finalize(self, wsgi_file_wrapper):
        """ Finalizes the response to prepare it for transmission

        Notes:
            This argument performs all necessary processing
            on the response object to prepare it to be sent
            to the WSGI server.  This includes setting
            Content-Length, wrapping the response's file
            descriptor as described in PEP333, and converting
            the response body to an interable

        Args:
            wsgi_file_wrapper: Wrapping function provided by WSGI server

        """

        if self.body:
            self.headers['Content-Length'] = str(len(self.body))
            if PY3:  # pragma: no cover
                self.iterable = [bytes(self.body, 'utf-8')]
            else:  # pragma: no cover
                self.iterable = [self.body]
        elif self.file:
            if self.file_len:
                self.headers['Content-Length'] = str(self.file_len)
            if wsgi_file_wrapper:
                self.iterable = wsgi_file_wrapper(self.file, 8 * 1024)
            else:
                self.iterable = iter(lambda: self.file.read(8 * 1024), b'')
        else:
            self.iterable = []
