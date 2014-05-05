from Distill import PY3


class Response(object):
    def __init__(self, status="200 OK"):
        self.status = status
        self.headers = {}
        self.body = None
        self.file = None
        self.file_len = None
        self.iterable = None

    @property
    def wsgi_headers(self):
        if PY3: # pragma: no cover
            return list(self.headers.items())
        return self.headers.items()

    def finalize(self, wsgi_file_wrapper):
        if self.body:
            self.headers['Content-Length'] = str(len(self.body))
        elif self.file:
            if self.file_len:
                self.headers['Content-Length'] = str(self.file_len)
        if self.body:
            if PY3:  # pragma: no cover
                self.iterable = [bytes(self.body, 'utf-8')]
            else:  # pragmo: no cover
                self.iterable = [self.body]
        elif self.file:
            if wsgi_file_wrapper:
                self.iterable = wsgi_file_wrapper(self.file, 8 * 1024)
            else:
                self.iterable = iter(lambda: self.file.read(8 * 1024), b'')
        else:
            self.iterable = []