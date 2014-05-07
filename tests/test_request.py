try:
    import testtools as unittest
except ImportError:
    import unittest
from Distill.request import Request

try:
    from StringIO import StringIO
    from io import BytesIO
except ImportError:
    from io import StringIO, BytesIO

form = b"""--AaB03x
Content-Disposition: form-data; name="submit-name"

Larry
--AaB03x
Content-Disposition: form-data; name="files"; filename="file1.txt"
Content-Type: text/plain

Hello world
--AaB03x--"""


class TestRequest(unittest.TestCase):
    def test_base_request(self):
        post_data = 'hello=world&foo=foo%20bar&baz=foo+bar'
        fake_env = {'wsgi.input': StringIO(post_data), 'wsgi.errors': None, 'wsgi.url_scheme': 'https',
                    'CONTENT_LENGTH': len(post_data), 'PATH_INFO': '/foo/bar', 'SERVER_PORT': '8080',
                    'CONTENT_TYPE': 'application/x-www-form-urlencoded', 'HTTP_X_H_Test': 'Foobar',
                    'HTTP_CONTENT_TYPE': 'application/x-www-form-urlencoded', 'QUERY_STRING': post_data,
                    'HTTP_HOST': 'foobar.baz:8080', 'SERVER_NAME': 'foobar.baz', 'HTTP_FOO': 'bar',
                    'SCRIPT_NAME': '/some/script/dir', 'REQUEST_METHOD': 'POST'}
        req = Request(fake_env)
        self.assertEqual(req.method, 'POST')
        self.assertEqual(req.POST['hello'], 'world')
        self.assertEqual(req.POST['foo'], 'foo bar')
        self.assertEqual(req.GET['hello'], 'world')
        self.assertEqual(req.GET['foo'], 'foo bar')
        self.assertEqual(req.GET['baz'], 'foo bar')
        self.assertEqual(req.server, 'foobar.baz:8080')
        self.assertIn('X-H-Test', req.headers)
        self.assertEqual(req.headers['X-H-Test'], 'Foobar')
        self.assertEqual(req.get_url('/foo/bar'), 'https://foobar.baz:8080/some/script/dir/foo/bar')

        del fake_env['CONTENT_TYPE']
        del fake_env['HTTP_HOST']
        fake_env['PATH_INFO'] += "/"
        fake_env['wsgi.input'].seek(0)
        req = Request(fake_env)
        self.assertEqual(req.POST['hello'], 'world')
        self.assertEqual(req.POST['foo'], 'foo bar')
        self.assertEqual(req.GET['hello'], 'world')
        self.assertEqual(req.GET['foo'], 'foo bar')
        self.assertEqual(req.server, 'foobar.baz:8080')
        self.assertEqual(req.get_url('/foo/bar'), 'https://foobar.baz:8080/some/script/dir/foo/bar')

        del fake_env['HTTP_CONTENT_TYPE']
        del fake_env['CONTENT_LENGTH']
        del fake_env['QUERY_STRING']
        fake_env['PATH_INFO'] = None
        fake_env['wsgi.input'].seek(0)
        fake_env['HTTP_COOKIE'] = 'foo=bar; bar=foo'
        req = Request(fake_env)
        self.assertNotIn('hello', req.POST)
        self.assertNotIn('hello', req.GET)
        self.assertEqual(req.server, 'foobar.baz:8080')
        self.assertEqual(req.get_url('/foo/bar'), 'https://foobar.baz:8080/some/script/dir/foo/bar')
        self.assertIn('foo', req.cookies)
        self.assertIn('bar', req.cookies)
        self.assertEqual(req.cookies['foo'], 'bar')

    def test_multipart_form(self):
        fake_env = {'wsgi.input': BytesIO(form), 'wsgi.errors': None, 'wsgi.url_scheme': 'https',
                    'CONTENT_LENGTH': len(form), 'PATH_INFO': '/foo/bar', 'SERVER_PORT': '8080',
                    'CONTENT_TYPE': 'multipart/form-data; boundary=AaB03x',
                    'HTTP_CONTENT_TYPE': 'multipart/form-data; boundary=AaB03x',
                    'HTTP_X_H_Test': 'Foobar', 'QUERY_STRING': '', 'HTTP_HOST': 'foobar.baz:8080',
                    'SERVER_NAME': 'foobar.baz', 'HTTP_FOO': 'bar', 'SCRIPT_NAME': '/some/script/dir',
                    'REQUEST_METHOD': 'POST'}
        req = Request(fake_env)
        self.assertEqual(req.POST['files'].filename, 'file1.txt')
        self.assertEqual(req.POST['files'].file.read(), b'Hello world')