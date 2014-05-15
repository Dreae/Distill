try:
    import testtools as unittest
except ImportError:
    import unittest

from functools import reduce
from distill.response import Response
from io import BytesIO


class TestResponse(unittest.TestCase):
    def test_finalize(self):
        resp = Response()
        resp.body = "Foobar"
        resp.finalize(None)
        self.assertEqual(resp.body, "Foobar")
        self.assertEqual(resp.wsgi_headers, [('Content-Length', str(len(resp.body)))])

        resp = Response("404 Not Found")
        resp.file = BytesIO(b"Foobar")
        resp.finalize(None)
        self.assertEqual([block for block in resp.iterable], [b'Foobar'])

        resp = Response()
        resp.file = BytesIO(b"Foobar")
        resp.finalize(lambda f, blocksize: iter(lambda: f.read(8 * 1024), b''))
        self.assertEqual([block for block in resp.iterable], [b'Foobar'])

    def test_body(self):
        resp = Response()
        resp.finalize(None)
        self.assertTrue(not resp.iterable)

        resp = Response()
        resp.file = BytesIO(b"Foobar")
        resp.file_len = len("Foobar")
        resp.finalize(None)
        self.assertEqual(resp.headers['Content-Length'], str(len('Foobar')))

    def test_set_cookie(self):
        resp = Response()
        resp.set_cookie("foo", "bar")
        resp.set_cookie("bar", "baz", domain='foo.com', secure=True, comment='Hello world')
        resp.set_cookie("foobar", "boofar", domain='.foo.com')
        self.assertEqual(reduce(lambda t, l: t + 1 if l[0] == 'Set-Cookie' else t, resp.wsgi_headers, 0), 3)