import unittest
from Distill.response import Response
import StringIO


class TestResponse(unittest.TestCase):
    def test_finalize(self):
        resp = Response()
        resp.body = "Foobar"
        resp.finalize(None)
        self.assertEqual(resp.body, "Foobar")
        self.assertEqual(resp.wsgi_headers, [('Content-Length', str(len(resp.body)))])

        resp = Response("404 Not Found")
        resp.file = StringIO.StringIO("Foobar")
        resp.finalize(None)
        self.assertEqual([block for block in resp.iterable], ['Foobar'])

        resp = Response()
        resp.file = StringIO.StringIO("Foobar")
        resp.finalize(lambda f, blocksize: iter(lambda: f.read(8 * 1024), b''))
        self.assertEqual([block for block in resp.iterable], ['Foobar'])

    def test_body(self):
        resp = Response()
        resp.finalize(None)
        self.assertTrue(not resp.iterable)

        resp = Response()
        resp.file = StringIO.StringIO("Foobar")
        resp.file_len = len("Foobar")
        resp.finalize(None)
        self.assertEqual(resp.headers['Content-Length'], str(len('Foobar')))

def suite():
    return unittest.TestSuite(map(TestResponse, ['test_finalize', 'test_body']))