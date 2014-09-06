import os
import shutil
from distill.request import Request
from distill.response import Response
from distill.sessions import UnencryptedLocalSessionStorage

try:
    import testtools as unittest
except ImportError:
    import unittest


class TestSessions(unittest.TestCase):
    def test_unencrypted_local_storage(self):
        store = os.path.abspath(os.path.join(os.path.dirname(__file__), 'sess'))
        if os.path.exists(store):
            shutil.rmtree(store)
        factory = UnencryptedLocalSessionStorage({'distill.sessions.directory': store})
        self.assertTrue(os.path.exists(store))

        class FakeApp(object):
            settings = {}
            map = None

        fake_env = {'wsgi.input': None, 'wsgi.errors': None, 'wsgi.url_scheme': 'https',
                    'CONTENT_LENGTH': '0', 'PATH_INFO': '/foo/bar', 'SERVER_PORT': '8080',
                    'CONTENT_TYPE': '', 'HTTP_X_H_Test': 'Foobar',
                    'HTTP_CONTENT_TYPE': '', 'QUERY_STRING': 'foo=bar&bar=baz',
                    'HTTP_HOST': 'foobar.baz:8080', 'SERVER_NAME': 'foobar.baz', 'HTTP_FOO': 'bar',
                    'SCRIPT_NAME': '/some/script/dir', 'REQUEST_METHOD': 'GET'}

        req = Request(fake_env, FakeApp)
        resp = Response()
        req.session = factory(req)
        self.assertEqual(len(req.session), 0)
        req.session['Foo'] = 'bar'
        req.session['Bar'] = 'foo'

        req.session.flash('test', 'test')
        queue = req.session.peek_flash('test')
        self.assertEqual(queue, ['test'])
        self.assertIn('_f_test', req.session)
        req.session.flash('test', 'test')
        req.session.flash('test', 'test', allow_duplicate=False)
        queue = req.session.pop_flash('test')
        self.assertEqual(queue, ['test', 'test'])
        self.assertNotIn('_f_test', req.session)

        token = req.session.get_csrf_token()
        self.assertEqual(req.session['__csrft__'], token)
        req.session.new_csrf_token()
        self.assertNotEqual(req.session.get_csrf_token(), token)

        for f in req.resp_callbacks:
            f(req, resp)
        self.assertEqual(len(resp.headers), 1)

        files = []
        for (dirpath, dirnames, filenames) in os.walk(store):
            files += filenames
            break

        req = Request(fake_env, FakeApp)
        req.cookies['ssid'] = files[0]
        resp = Response()
        req.session = factory(req)
        self.assertIn('Foo', req.session)
        self.assertFalse(req.session.dirty)
        req.session.save(resp)
        req.session.changed()
        self.assertTrue(req.session.dirty)
        req.session['Foo'] = 'Bar'
        req.session.invalidate()
        self.assertTrue(req.session.invalid)
        for f in req.resp_callbacks:
            f(req, resp)
        self.assertFalse(os.path.isfile(os.path.join(store, files[0])))

        req = Request(fake_env, FakeApp)
        req.cookies['ssid'] = files[0]
        req.session = factory(req)
        self.assertNotIn('ssid', req.cookies)