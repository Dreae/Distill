import os

try:
    import testtools as unittest
except ImportError:
    import unittest
import json
from distill.decorators import before, after
from distill.exceptions import HTTPNotFound, HTTPBadRequest, HTTPErrorResponse, HTTPInternalServerError
from distill.application import Distill
from distill.renderers import renderer, JSON
from distill.response import Response

from routes import Mapper

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def do_before(request, response):
    response.headers['X-Before'] = 'true'


def do_after(request, response):
    response.headers['X-After'] = 'true'


@before(do_before)
@after(do_after)
@renderer('login.mako')
def POST_home(request, response):
    return {'user': request.POST['user']}


@before(do_before)
@after(do_after)
@renderer('site.mako')
def GET_home(request, response):
    return {}


@renderer('prettyjson')
def bad_request(request, response):
    return {'msg': "Well that was bad"}


def userinfo(request, reponse):
    if request.method == 'POST':
        return HTTPErrorResponse("716 I am a teapot")

    class User(object):
        def __init__(self, user):
            self.user = user

        def json(self, request):
            return {'username': self.user}

    return User(request.matchdict['user'])


def user(request, response):
    resp = Response(headers={'X-Test': 'Foobar'})
    resp.body = "Hello world"
    return resp


def internal_server_error(request, response):
    raise HTTPInternalServerError()


def handle_ise(request, response):
    print(response.description)
    resp = Response()
    resp.body = "Whoops"
    return resp


def create_bad_request(request, response):
    return HTTPBadRequest()


def cont_do_before(controller, request, response):
    response.headers['X-Before'] = 'true'


def cont_do_after(controller, request, response):
    response.headers['X-After'] = 'true'


class TestController(object):
    @renderer('prettyjson')
    @before(cont_do_before)
    @after(cont_do_after)
    def GET_home(self, request, response):
        return {'data': True}


exc_info = None


class TestApplication(unittest.TestCase):
    def test_application(self):
        app = Distill(settings={
            'distill.document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'res')),
            'distill.sessions.factory': 'distill.sessions.UnencryptedLocalSessionStorage',
            'distill.sessions.directory': os.path.abspath(os.path.join(os.path.dirname(__file__), 'sess'))
        }, controllers={'testcontrollerinit': TestController}
        )
        app.add_renderer('prettyjson', JSON(indent=4))
        app.add_controller('testcontroller', TestController)
        app.add_controller('testcontroller2', TestController())
        app.on_except(HTTPBadRequest, bad_request)
        app.on_except(HTTPInternalServerError, handle_ise)
        app.map_connect('home', '/', action=GET_home, conditions={"method": ["GET"]})
        app.map_connect('home', '/', action=POST_home, conditions={"method": ["POST"]})
        app.map_connect('badrequest', '/badrequest', action=create_bad_request)
        app.map_connect('userinfo', '/:user/userinfo', action=userinfo)
        app.map_connect('ise', '/internalservererror', action=internal_server_error)
        app.map_connect('homecontroller', '/controller', action='GET_home', controller='testcontroller')
        app.map_connect('homecontroller1', '/controller2', action='GET_home', controller='testcontroller2')
        app.map_connect('homecontroller1', '/controllerinit', action='GET_home', controller='testcontrollerinit')
        app.map_connect('homecontroller2', '/controllerNA', action='GET_home', controller='nocontroller')
        app.map_connect('homecontroller3', '/actionNA', action='noaction', controller='testcontroller')
        app.map_connect('user', '/:user', action=user)

        resp, body = self.simulate_request(app, 'GET', '', None, '')
        self.assertIn('X-Before', resp.headers)
        self.assertIn('X-After', resp.headers)
        self.assertRaises(HTTPNotFound, self.simulate_request, app, 'GET', '/foo/bar/baz', None, '')

        resp, body = self.simulate_request(app, 'GET', '/controller', None, '')
        self.assertIn('X-Before', resp.headers)
        self.assertIn('X-After', resp.headers)
        data = json.loads(body)
        self.assertTrue(data['data'])

        resp, body = self.simulate_request(app, 'GET', '/controllerinit', None, '')
        self.assertIn('X-Before', resp.headers)
        self.assertIn('X-After', resp.headers)
        data = json.loads(body)
        self.assertTrue(data['data'])

        self.assertRaises(HTTPNotFound, self.simulate_request, app, 'GET', '/controllerNA', None, '')
        self.assertRaises(HTTPNotFound, self.simulate_request, app, 'GET', '/actionNA', None, '')

        resp, body = self.simulate_request(app, 'GET', '/controller2', None, '')
        self.assertIn('X-Before', resp.headers)
        self.assertIn('X-After', resp.headers)
        data = json.loads(body)
        self.assertTrue(data['data'])

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
        def test_before1(request, response):
            response.headers['X-Before1'] = 'true'

        def test_after1(request, response):
            response.headers['X-After1'] = 'true'

        def test_before2(request, response):
            response.headers['X-Before2'] = 'true'

        def test_after2(request, response):
            response.headers['X-After2'] = 'true'

        map_ = Mapper()
        map_.connect('userinfo', '/:user/userinfo', action=userinfo)
        map_.connect('ise', '/internalservererror', action=internal_server_error)
        app = Distill(rmap=map_)
        app.use(test_before1)
        app.use(test_before2)
        app.use(test_after1, before=False)
        app.use(test_after2, before=False)

        app.add_renderer('prettyjson', JSON(indent=4))
        app.on_except(HTTPInternalServerError, handle_ise)

        resp, body = self.simulate_request(app, 'GET', '/Dreae/userinfo', None, '')
        self.assertIn('X-Before1', resp.headers)
        self.assertEqual(resp.headers['X-Before1'], 'true')
        self.assertIn('X-After1', resp.headers)
        self.assertEqual(resp.headers['X-After1'], 'true')
        self.assertIn('X-Before2', resp.headers)
        self.assertEqual(resp.headers['X-Before2'], 'true')
        self.assertIn('X-After2', resp.headers)
        self.assertEqual(resp.headers['X-After2'], 'true')

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

        def start_response(status, headers, exc_info_=None):
            resp.status = status
            resp.headers = dict(headers)
            global exc_info
            exc_info = exc_info_

        body = app(fake_env, start_response)

        if exc_info:
            raise exc_info[0](exc_info[1])  # No traceback because python3

        body = body[0]
        return resp, body.decode('utf-8')


if __name__ == '__main__':
    unittest.main()