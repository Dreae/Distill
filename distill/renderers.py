from functools import wraps
from mako.lookup import TemplateLookup
from distill import PY2
import json
from distill.exceptions import HTTPInternalServerError


class RenderFactory(object):
    """
    This class provides a wrapper for handling rendering operations

    """
    _factory = None

    def __init__(self, settings):
        """ Init
         Args:
            settings: The application's settings dict
        """
        if PY2:  # pragma: no cover
            self._template_lookup = TemplateLookup(output_encoding='ascii')
        else:  # pragma: no cover
            self._template_lookup = TemplateLookup(input_encoding='utf-8')
        self._template_lookup.directories.append(settings.get('distill.document_root', ''))
        self._template_lookup.module_directory = settings.get('distill.document_root', '')
        self._renderers = {}

    def __call__(self, template, data, request, response):
        """ Actually render the response

        Notes:
            The current request will be available to template
            template as req

        Args:
            template: The template you're looking up
            data: The data to be passed to the template
            request: Current request
            response: Current response
        """
        if '.mako' == template.lower()[-5:]:
            response.headers['Content-Type'] = 'text/html'
            data['req'] = request
            return self._template_lookup.get_template(template).render(**data)
        elif template in self._renderers:
            return self._renderers[template](data, request, response)
        raise HTTPInternalServerError(description="Missing template file {0}".format(template))

    def register_renderer(self, name, serializer):
        """Adds template to the current instances renderers dict"""
        self._renderers[name] = serializer

    @staticmethod
    def create(settings):
        """Initializes the RenderFactory"""
        RenderFactory._factory = RenderFactory(settings)
        RenderFactory._factory.register_renderer('json', JSON())

    @staticmethod
    def render(template, data, request, response):
        """Returns the rendered response to a template"""
        return RenderFactory._factory(template, data, request, response)

    @staticmethod
    def add_renderer(name, serializer):
        """Adds a template to the RenderFactory"""
        RenderFactory._factory.register_renderer(name, serializer)


def renderer(template):
    """ Decorator for rendering responses

    Notes:
        When using this decorator the returned value of
        on_get or on_post is treated as arguments passed
        to the template, as such their meaning will vary
        accordingly
    """
    def _render(method):
        @wraps(method)
        def _call(request, response):
            data = method(request, response)
            return RenderFactory.render(template, data, request, response)
        return _call
    return _render


class JSON(object):
    def __init__(self, serializer=json.dumps, **kwargs):
        """ Init
         Args:
            serializer: The serialzer to be used to stringify the object
            kwargs: All kwargs will be passed to the serializer
        """
        self.serializer = serializer
        self.kw = kwargs

    def __call__(self, data, request, response):
        """ Render the response to the template

        Notes:
            Templates should be callables that accept the
            following arguments and return either a string
            representing the rendered response body, or a
            new response

        Args:
            data: The data to be rendered
            request: The current request, to be used as needed
            response: The current response

        """
        if type(data) in [dict, list]:
            response.headers['Content-Type'] = 'application/json'
            return self.serializer(data, **self.kw)
        elif hasattr(data, 'json'):
            response.headers['Content-Type'] = 'application/json'
            return self.serializer(data.json(request), **self.kw)
        else:
            raise HTTPInternalServerError(description="{0} is not JSON serializable".format(data.__repr__()))
