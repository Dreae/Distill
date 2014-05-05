import os
import unittest
import json
from StringIO import StringIO
from Distill.exceptions import HTTPNotFound, HTTPBadRequest, HTTPErrorResponse, HTTPInternalServerError
from Distill.application import Distill, exception_responder
from Distill.renderers import renderer, JSON
from Distill.response import Response


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

    @renderer('site.mako')
    def on_get(self, request, response):
        return {}

    @renderer('login.mako')
    def on_post(self, request, response):
        return {'user': request.POST['user']}

    @renderer('prettyjson')
    @exception_responder(HTTPBadRequest)
    def handle_bad_request(self, request, response):
        return {"msg": "Well that was bad"}

    @exception_responder(HTTPInternalServerError)
    def handle_ise(self, request, response):
        return Response('200 OK')


class TestApplication(unittest.TestCase):
    def test_application(self):
        app = Distill(base_node=Website(),
                      settings={
                          'distill.document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'res'))})
        app.add_renderer('prettyjson', JSON(indent=4))
        self.simulate_request(app, 'GET', '', None, '')
        with self.assertRaises(HTTPNotFound):
            self.simulate_request(app, 'GET', '/foo/bar/baz', None, '')

        resp, body = self.simulate_request(app, 'GET', '/badrequest', None, '')
        data = json.loads(body[0])
        self.assertEqual(data['msg'], 'Well that was bad')
        self.assertEqual(resp.status, '400 Bad Request')

        resp, body = self.simulate_request(app, 'POST', '', 'foo=bar', 'user=Bar')
        self.assertEqual(body[0], 'Loggedin Bar')

        with self.assertRaises(HTTPErrorResponse):
            self.simulate_request(app, 'POST', '/Foo/userinfo', None, '')

        resp, body = self.simulate_request(app, 'GET', '/Foo', None, '')
        self.assertIn('X-Test', resp.headers)
        self.assertEqual(body[0], 'Hello world')

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
                raise exc_info[0], exc_info[1], exc_info[2]

        body = app(fake_env, start_response)
        return resp, body


def suite():
    return unittest.TestSuite(map(TestApplication, ['test_application']))