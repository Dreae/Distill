from Distill import PY3


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
            return list(self.headers.items())
        return self.headers.items()  # pragma: no cover

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
