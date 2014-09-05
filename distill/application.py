import sys
from functools import partial
from routes import Mapper
from distill.exceptions import HTTPNotFound, HTTPErrorResponse
from distill.request import Request
from distill.response import Response
from distill.renderers import RenderFactory


class Distill(object):
    def __init__(self, rmap=None, settings=None):
        """ INIT

        Args:
            base_node: The root of the traversal tree
            before: Method to be called before the view is called
            after: Method to be called after the view is called
            settings: Settings dictionary, will be available in all requests
            document_root: Root directory for mako templates
        """
        if rmap is None:
            self.map = Mapper()
        else:
            self.map = rmap

        if settings is None:
            settings = {}

        if 'distill.sessions.factory' in settings:
            components = settings['distill.sessions.factory'].split('.')
            mod = __import__('.'.join(components[:-1]), globals(), locals(), components[-1:])
            self._session_factory = getattr(mod, components[len(components) - 1])(settings)
        else:
            self._session_factory = None

        self.settings = settings
        self._before = []
        self._after = []
        self._exc_listeners = {}

        RenderFactory.create(settings)

    def __call__(self, env, start_response):
        """ Excpected WSGI method

        Creates new request using the provided env, then traverses
        the root node to the required view node
        """
        req = Request(env, self)

        if self._session_factory:
            self._session_factory.load(req)

        try:
            resp = self._request(env, req)
        except HTTPErrorResponse as ex:
            if self._exc_listeners and ex.__class__ in self._exc_listeners:
                resp = Response(ex.status, ex.headers)
                res = self._exc_listeners[ex.__class__](req, resp)
                if isinstance(res, Response):
                    resp = res
                else:
                    resp.body = str(res)

                if self._session_factory:
                    self._session_factory.save(req, resp)
                resp.finalize(env.get('wsgi.file_wrapper'))
                start_response(resp.status, resp.wsgi_headers)
                return resp.iterable
            else:
                if self._session_factory:
                    self._session_factory.save(req, ex)
                start_response(ex.status, ex.wsgi_headers, sys.exc_info())
                # By spec execution shouldn't get here, but incase it does
                return []  # pragma: no cover

        if self._session_factory:
            self._session_factory.save(req, resp)

        start_response(resp.status, resp.wsgi_headers)
        return resp.iterable

    def _request(self, env, req):
        """ Processes the request
         Notes:
            This method acts as a wrapper to ease exception handling

        Args:
            env: The wsgi environ variable
        """
        resp = Response()

        self._do_before(req, resp)

        context = self.map.match(req.path, env)

        if context is not None:
            req.matchdict = context
            res = context['action'](req, resp)
            if isinstance(res, Response):
                if isinstance(res, HTTPErrorResponse):
                    raise res
                resp = res
            else:
                resp.body = str(res)

            self._do_after(req, resp)
        else:
            raise HTTPNotFound()

        resp.finalize(env.get('wsgi.file_wrapper'))
        return resp

    def _do_before(self, req, resp):
        if self._before:
            def next_(n):
                if n == len(self._before):
                    return
                self._before[n](req, resp, partial(next_, n + 1))

            self._before[0](req, resp, partial(next_, 1))

    def _do_after(self, req, resp):
        if self._after:
            def next_(n):
                if n == len(self._after):
                    return
                self._after[n](req, resp, partial(next_, n + 1))

            self._after[0](req, resp, partial(next_, 1))

    def use(self, function, before=True):
        if not before:
            self._after.append(function)
        else:
            self._before.append(function)

    def map_connect(self, *args, **kwargs):
        self.map.connect(*args, **kwargs)

    def on_except(self, exc, method):
        self._exc_listeners[exc] = method

    @staticmethod
    def add_renderer(name, serializer):
        RenderFactory.add_renderer(name, serializer)
