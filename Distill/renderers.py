from functools import wraps
from mako.lookup import TemplateLookup
from Distill import PY2
import json
from Distill.exceptions import HTTPInternalServerError


class RenderFactory(object):
    _factory = None

    def __init__(self, settings):
        if PY2:  # pragma: no cover
            self._template_lookup = TemplateLookup(output_encoding='ascii')
        else:  # pragma: no cover
            self._template_lookup = TemplateLookup(input_encoding='utf-8')
        self._template_lookup.directories.append(settings.get('distill.document_root', None))
        self._template_lookup.module_directory = settings.get('distill.document_root', None)
        self._renderers = {}

    def __call__(self, template, data, request, response):
        if '.mako' in template.lower():
            response.headers['Content-Type'] = 'text/html'
            return self._template_lookup.get_template(template).render(**data)
        elif template in self._renderers:
            return self._renderers[template](data, request, response)
        raise HTTPInternalServerError(description="Missing template file {0}".format(template))

    def register_renderer(self, name, serializer):
        self._renderers[name] = serializer

    @staticmethod
    def create(settings):
        RenderFactory._factory = RenderFactory(settings)
        RenderFactory._factory.register_renderer('json', JSON())

    @staticmethod
    def render(template, data, request, response):
        return RenderFactory._factory(template, data, request, response)

    @staticmethod
    def add_renderer(name, serializer):
        RenderFactory._factory.register_renderer(name, serializer)


def renderer(template):
    def _render(method):
        @wraps(method)
        def _call(context, request, response):
            data = method(context, request, response)
            return RenderFactory.render(template, data, request, response)
        return _call
    return _render


class JSON(object):
    def __init__(self, serializer=json.dumps, **kwargs):
        self.serializer = serializer
        self.kw = kwargs

    def __call__(self, data, request, response):
        if type(data) in [dict, list]:
            response.headers['Content-Type'] = 'application/json'
            return self.serializer(data, **self.kw)
        elif hasattr(data, 'json'):
            response.headers['Content-Type'] = 'application/json'
            return self.serializer(data.json(request), **self.kw)
        else:
            raise HTTPInternalServerError(description="{0} is not JSON serializable".format(data.__repr__()))