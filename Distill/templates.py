from functools import wraps
from mako.lookup import TemplateLookup
import sys
from Distill import PY2

if PY2:
    _template_lookup = TemplateLookup(output_encoding='ascii')
else:
    _template_lookup = TemplateLookup(input_encoding="utf-8")


def template_settings(settings):
    _template_lookup.directories.append(settings.get('document_root', None))
    _template_lookup.module_directory = settings.get('document_root', None)


def renderer(template):
    def _render(method):
        @wraps(method)
        def _call(context, request, response):
            response.headers['Content-Type'] = 'text/html'
            data = method(context, request, response)
            return _template_lookup.get_template(template).render(**data)
        return _call
    return _render