import json
import os
try:
    import testtools as unittest
except ImportError:
    import unittest
from distill.exceptions import HTTPInternalServerError
from distill.renderers import RenderFactory, renderer
from distill.response import Response


class TestRenderers(unittest.TestCase):
    def test_default_renderers(self):
        RenderFactory.create({})

        @renderer('json')
        def fake_on_get_json(request, response):
            return {"Hello": "world"}

        resp = Response()
        rendered = fake_on_get_json(None, resp)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')
        data = json.loads(rendered)
        self.assertEqual(data['Hello'], 'world')

        class json_obj(object):
            def __init__(self, name):
                self.name = name

            def json(self, requst):
                return {'name': self.name}

        class not_json_obj(object):
            pass

        @renderer('json')
        def fake_on_get_json_obj(request, response):
            return json_obj('Foobar')

        @renderer('json')
        def fake_on_get_non_json_obj(request, response):
            return not_json_obj()

        @renderer('json')
        def fake_on_return_response(request, response):
            return Response("719 I am not a teapot")

        @renderer('json', pad=True)
        def test_secure_pad(request, response):
            return {"foo": "bar"}

        resp = Response()
        rendered = fake_on_get_json_obj(None, resp)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')
        data = json.loads(rendered)
        self.assertEqual(data['name'], 'Foobar')
        self.assertRaises(TypeError, fake_on_get_non_json_obj, None, Response())
        self.assertIsInstance(fake_on_return_response(None, None), Response)

        resp = Response()
        rendered = test_secure_pad(None, resp)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')
        self.assertEqual(rendered, ")]}',\n" + json.dumps({"foo": "bar"}))

    def test_file_templates(self):
        RenderFactory.create(
            {'distill.document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'res'))})

        @renderer('test.mako')
        def fake_on_get_json(request, response):
            return {"user": "Foobar"}

        @renderer('test.mako')
        def fake_on_get_string(request, response):
            return "Hello world!"


        resp = Response()
        rendered = fake_on_get_json(None, resp)
        self.assertEqual(resp.headers['Content-Type'], 'text/html')
        self.assertEqual(rendered, 'Hello Foobar!')

        resp = Response()
        rendered = fake_on_get_string(None, resp)
        self.assertEqual(rendered, 'Hello world!')

    def test_add_renderer(self):
        RenderFactory.create({})

        class TextRenderer(object):
            def __init__(self):
                pass

            def __call__(self, data, request, response):
                response.headers['Content-Type'] = 'text/plain'
                return str(data)

        RenderFactory.add_renderer('text2', TextRenderer())

        @renderer('text2')
        def fake_on_get(request, response):
            return "Hello world"

        resp = Response()
        rendered = fake_on_get(None, resp)
        self.assertEqual(resp.headers['Content-Type'], 'text/plain')
        self.assertEqual(rendered, 'Hello world')

    def test_no_template(self):
        RenderFactory.create({})

        @renderer('foobar')
        def fake_on_get(request, response):
            return "How did I get here?"

        self.assertRaises(HTTPInternalServerError, fake_on_get, None, None)
