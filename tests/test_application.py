import os
from distill.sessions import BaseSessionFactory

try:
    import testtools as unittest
except ImportError:
    import unittest
import json
from distill.decorators import exception_responder, before, after
from distill.exceptions import HTTPNotFound, HTTPBadRequest, HTTPErrorResponse, HTTPInternalServerError
from distill.application import Distill
from distill.renderers import renderer, JSON
from distill.response import Response

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class BlankSessionFactory(BaseSessionFactory):
    def save(self, request, response):
        pass

    def load(self, request):
        pass

    def __init__(self, settings):
        pass


class User(object):
    def __init__(self, username):
        self.username = username

    def __getitem__(self, item):
        if item == 'userinfo':
            return UserInfo(self)

    def on_get(self, request, response):
        resp = Response("200 OK", {'X-Test': 'Foobar'})
        resp.body = 'Hello world'
        return resp


class UserInfo(object):
    def __init__(self, user):
        self.user = user

    def json(self, request):
        return {"username": self.user.username}

    @renderer('prettyjson')
    def on_get(self, request, response):
        return self

    def on_post(self, request, response):
        return HTTPErrorResponse("716 I am a teapot")


class Website(object):
    def __getitem__(self, item):
        if item == 'badrequest':
            raise HTTPBadRequest()
        elif item == 'internalservererror':
            raise HTTPInternalServerError()
        return User(item)

    def do_before(self, request, response):
        response.headers['X-Before'] = 'true'

    def do_after(self, request, response):
        response.headers['X-After'] = 'true'

    @before(do_before)
    @after(do_after)
    @renderer('site.mako')
    def on_get(self, request, response):
        return {}

    def do_after(self, request, response):
        response.headers['X-After'] = 'true'

    @renderer('login.mako')
    def on_post(self, request, response):
        return {'user': request.POST['user']}

    @renderer('prettyjson')
    @exception_responder(HTTPBadRequest)
    def handle_bad_request(self, request, response):
        return {"msg": "Well that was bad"}

    @exception_responder(HTTPInternalServerError)
    def handle_ise(self, request, response):
        resp = Response('200 OK')
        resp.body = "Whoops"
        return resp


class TestApplication(unittest.TestCase):
    def test_application(self):
        app = Distill(base_node=Website(),
                      settings={
                          'distill.document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'res')),
                          'distill.sessions.factory': 'distill.sessions.UnencryptedLocalSessionStorage',
                          'distill.sessions.directory': os.path.abspath(os.path.join(os.path.dirname(__file__), 'sess'))
                      })
        app.add_renderer('prettyjson', JSON(indent=4))
        resp, body = self.simulate_request(app, 'GET', '', None, '')
        self.assertIn('X-Before', resp.headers)
        self.assertIn('X-After', resp.headers)
        self.assertRaises(HTTPNotFound, self.simulate_request, app, 'GET', '/foo/bar/baz', None, '')

        resp, body = self.simulate_request(app, 'GET', '/badrequest', None, '')
        data = json.loads(body)
        self.assertEqual(data['msg'], 'Well that was bad')
        self.assertEqual(resp.status, '400 Bad Request')

        resp, body = self.simulate_request(app, 'POST', '', 'foo=bar', 'user=Bar')
        self.assertEqual(body, 'Loggedin Bar')

        self.assertRaises(HTTPErrorResponse, self.simulate_request, app, 'POST', '/Foo/userinfo', None, '')

        resp, body = self.simulate_request(app, 'GET', '/Foo', None, '')
        self.assertIn('X-Test', resp.headers)
        self.assertEqual(body, 'Hello world')

        resp, body = self.simulate_request(app, 'GET', '/internalservererror', None, '')
        self.assertEqual(resp.status, '200 OK')

    def test_before_after(self):
        def test_before(request, response):
            response.headers['X-Before'] = 'true'

        def test_after(request, response):
            response.headers['X-After'] = 'true'

        app = Distill(base_node=Website(), before=test_before, after=test_after)
        app.add_renderer('prettyjson', JSON(indent=4))

        resp, body = self.simulate_request(app, 'GET', '/Dreae/userinfo', None, '')
        self.assertIn('X-Before', resp.headers)
        self.assertEqual(resp.headers['X-Before'], 'true')
        self.assertIn('X-After', resp.headers)
        self.assertEqual(resp.headers['X-After'], 'true')

        self.assertRaises(HTTPErrorResponse, self.simulate_request, app, 'POST', '/Foo/userinfo', None, '')
        resp, body = self.simulate_request(app, 'GET', '/internalservererror', None, '')
        self.assertEqual(resp.status, '200 OK')

    @staticmethod
    def simulate_request(app, method, path, querystring, body):
        fake_env = {'wsgi.input': StringIO(body), 'wsgi.errors': None, 'wsgi.url_scheme': 'https',
                    'CONTENT_LENGTH': len(body), 'PATH_INFO': path, 'SERVER_PORT': '8080',
                    'CONTENT_TYPE': 'application/x-www-form-urlencoded', 'HTTP_X_H_Test': 'Foobar',
                    'HTTP_CONTENT_TYPE': 'application/x-www-form-urlencoded', 'QUERY_STRING': querystring,
                    'HTTP_HOST': 'foobar.baz:8080', 'SERVER_NAME': 'foobar.baz', 'HTTP_FOO': 'bar',
                    'SCRIPT_NAME': '/some/script/dir', 'REQUEST_METHOD': method}

        resp = Response()

        def start_response(status, headers, exc_info=None):
            resp.status = status
            resp.headers = dict(headers)
            if exc_info:
                raise exc_info[0](exc_info[1])  # No traceback because python3

        body = app(fake_env, start_response)
        body = body[0]
        return resp, body.decode('utf-8')
