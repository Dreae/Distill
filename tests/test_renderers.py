import json
import os
import unittest
from Distill.exceptions import HTTPInternalServerError
from Distill.renderers import RenderFactory, renderer
from Distill.response import Response


class TestRenderers(unittest.TestCase):
    def test_default_renderers(self):
        RenderFactory.create({})

        @renderer('json')
        def fake_on_get_json(this, request, response):
            return {"Hello": "world"}

        resp = Response()
        rendered = fake_on_get_json(None, None, resp)
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
        def fake_on_get_json_obj(this, request, response):
            return json_obj('Foobar')

        @renderer('json')
        def fake_on_get_non_json_obj(this, request, response):
            return not_json_obj()

        resp = Response()
        rendered = fake_on_get_json_obj(None, None, resp)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')
        data = json.loads(rendered)
        self.assertEqual(data['name'], 'Foobar')
        with self.assertRaises(HTTPInternalServerError):
            fake_on_get_non_json_obj(None, None, None)

    def test_file_templates(self):
        RenderFactory.create(
            {'distill.document_root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'res'))})

        @renderer('test.mako')
        def fake_on_get_json(this, request, response):
            return {"user": "Foobar"}

        resp = Response()
        rendered = fake_on_get_json(None, None, resp)
        self.assertEqual(resp.headers['Content-Type'], 'text/html')
        self.assertEqual(rendered, 'Hello Foobar!')

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
        def fake_on_get(this, request, response):
            return "Hello world"

        resp = Response()
        rendered = fake_on_get(None, None, resp)
        self.assertEqual(resp.headers['Content-Type'], 'text/plain')
        self.assertEqual(rendered, 'Hello world')


def suite():
    return unittest.TestSuite(
        map(TestRenderers, ['test_default_renderers', 'test_file_templates', 'test_add_renderer']))