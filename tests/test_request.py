try:
    import testtools as unittest
except ImportError:
    import unittest
from Distill.request import Request

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


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
        req = Request(fake_env)
        self.assertNotIn('hello', req.POST)
        self.assertNotIn('hello', req.GET)
        self.assertEqual(req.server, 'foobar.baz:8080')
        self.assertEqual(req.get_url('/foo/bar'), 'https://foobar.baz:8080/some/script/dir/foo/bar')


def suite():
    return unittest.TestSuite(map(TestRequest, ['test_base_request']))