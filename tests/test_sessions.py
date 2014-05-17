import os
import shutil
from distill.request import Request
from distill.response import Response
from distill.sessions import Session, UnencryptedLocalSessionStorage

try:
    import testtools as unittest
except ImportError:
    import unittest


class TestSessions(unittest.TestCase):
    def test_session_dict(self):
        sess = Session()
        sess['Foo'] = "bar"
        self.assertTrue(sess.changed)
        self.assertIn('Foo', sess)
        self.assertEqual(sess['Foo'], 'bar')

        sess = Session({"Foo": "Bar"})
        self.assertFalse(sess.changed)
        self.assertIn('Foo', sess)
        self.assertEqual(sess['Foo'], 'Bar')
        del sess['Foo']
        self.assertNotIn('Foo', sess)
        sess['Baz'] = {"Foo": "Bar"}
        self.assertTrue(sess.changed)
        self.assertEqual(len(sess), 1)

        sess = Session({"Foo": "Bar", "Baz": {"Foo": "Bar"}})
        self.assertEqual(sess['Baz'], {"Foo": "Bar"})
        sess['Baz']['Foo'] = 'Foobar'
        self.assertFalse(sess.changed)
        sess.modified()
        self.assertTrue(sess.changed)

        sess = Session({"Foo": "Bar"})
        self.assertFalse(sess.changed)
        sess.update({"Foo": "Baz"})
        self.assertTrue(sess.changed)
        self.assertEqual(sess['Foo'], 'Baz')
        sess.setdefault('Bar', 'Foo')
        self.assertEqual(sess['Bar'], 'Foo')
        sess.setdefault('Bar', 'Baz')
        self.assertNotEqual(sess['Bar'], 'Baz')
        self.assertEqual(sess.get('Bar', None), 'Foo')
        self.assertEqual(sess.get('Baz', None), None)
        sess.invalidate()
        self.assertTrue(sess.invalid)
        self.assertEqual(len(sess), 0)

        sess = Session({"Foo": "Bar"})
        self.assertEqual(dict(sess.items()), {"Foo": "Bar"})
        sess['Bar'] = 'Foo'
        for k in sess.keys():
            self.assertIn(k, ['Foo', 'Bar'])
        for v in sess.values():
            self.assertIn(v, ['Foo', 'Bar'])
        for k in sess:
            self.assertIn(k, sess.keys())

    def test_unencrypted_local_storage(self):
        store = os.path.abspath(os.path.join(os.path.dirname(__file__), 'sess'))
        if os.path.exists(store):
            shutil.rmtree(store)
        factory = UnencryptedLocalSessionStorage({'distill.sessions.directory': store})
        self.assertTrue(os.path.exists(store))

        fake_env = {'wsgi.input': None, 'wsgi.errors': None, 'wsgi.url_scheme': 'https',
                    'CONTENT_LENGTH': '0', 'PATH_INFO': '/foo/bar', 'SERVER_PORT': '8080',
                    'CONTENT_TYPE': '', 'HTTP_X_H_Test': 'Foobar',
                    'HTTP_CONTENT_TYPE': '', 'QUERY_STRING': 'foo=bar&bar=baz',
                    'HTTP_HOST': 'foobar.baz:8080', 'SERVER_NAME': 'foobar.baz', 'HTTP_FOO': 'bar',
                    'SCRIPT_NAME': '/some/script/dir', 'REQUEST_METHOD': 'GET'}

        req = Request(fake_env)
        resp = Response()
        factory.load(req)
        self.assertEqual(len(req.session), 0)
        req.session['Foo'] = 'bar'
        factory.save(req, resp)
        self.assertEqual(len(resp.headers), 1)

        files = []
        for (dirpath, dirnames, filenames) in os.walk(store):
            files += filenames
            break

        req = Request(fake_env)
        req.cookies['ssid'] = files[0]
        resp = Response()
        factory.load(req)
        self.assertIn('Foo', req.session)
        factory.save(req, resp)
        req.session['Foo'] = 'Bar'
        factory.save(req, resp)
        req.session.invalidate()
        factory.save(req, resp)
        self.assertFalse(os.path.isfile(os.path.join(store, files[0])))

        req = Request(fake_env)
        req.cookies['ssid'] = files[0]
        factory.load(req)
        self.assertNotIn('ssid', req.cookies)