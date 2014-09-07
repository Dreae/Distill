from inspect import isclass
import sys
from functools import partial
from routes import Mapper
from distill.exceptions import HTTPNotFound, HTTPErrorResponse
from distill.request import Request
from distill.response import Response
from distill.renderers import RenderFactory


class Distill(object):
    def __init__(self, rmap=None, settings=None, controllers=None):
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

        self._session_factory = None

        self.settings = settings
        self._before = []
        self._after = []
        self._exc_listeners = {}
        self._controllers = {}
        if controllers is not None:
            self._controllers.update(controllers)

        RenderFactory.create(settings)

    def __call__(self, env, start_response):
        """ Excpected WSGI method

        Creates new request using the provided env, then traverses
        the root node to the required view node
        """
        req = Request(env, self)

        if self._session_factory:
            req.session = self._session_factory(req)

        try:
            resp = self._request(env, req)
        except HTTPErrorResponse as ex:
            if self._exc_listeners and ex.__class__ in self._exc_listeners:
                resp = ex
                res = self._exc_listeners[ex.__class__](req, resp)
                if isinstance(res, Response):
                    resp = res
                else:
                    resp.body = str(res)

                resp.finalize(env.get('wsgi.file_wrapper'))
                start_response(resp.status, resp.wsgi_headers)
                return resp.iterable
            else:
                start_response(ex.status, ex.wsgi_headers, sys.exc_info())
                # By spec execution shouldn't get here, but incase it does
                return []  # pragma: no cover

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
        res = None

        if context is not None:
            req.matchdict = context
            if 'controller' in context and context['controller'] in self._controllers:
                if hasattr(self._controllers[context['controller']], context['action']):
                    cls = self._controllers[context['controller']]
                    controller = cls()
                    res = getattr(controller, context['action'])(req, resp)
                else:
                    raise HTTPNotFound()
            elif hasattr(context['action'], '__call__'):
                res = context['action'](req, resp)
            else:
                raise HTTPNotFound()

            if isinstance(res, Response):
                if isinstance(res, HTTPErrorResponse):
                    raise res
                resp = res
            elif res is not None:
                resp.body = str(res)

            self._do_after(req, resp)
        else:
            raise HTTPNotFound()

        resp.finalize(env.get('wsgi.file_wrapper'))
        return resp

    def _do_before(self, req, resp):
        if self._before:
            for f in self._before:
                f(req, resp)

    def _do_after(self, req, resp):
        if self._after:
            for f in self._after:
                f(req, resp)

        if req.resp_callbacks:
            for f in req.resp_callbacks:
                f(req, resp)

    def use(self, function, before=True):
        """ Adds a middleware to the application
        Notes:
            This method allows you to add middleware
            that will be called either before or after
            a request has been handled by the application
            The function should accept two positional arguments
            function(request, response)

        Args:
            function: The function to be called
            befre: Should the function be called before a request
        """
        if not before:
            self._after.append(function)
        else:
            self._before.append(function)

    def map_connect(self, *args, **kwargs):
        """ Adds a route to the routing table

        Notes:
            For further documentation see routes documection
            on the Mapper object:

            http://routes.readthedocs.org/en/latest/index.html

        Args:
            args: Positional arguments to be passed to the mapper
            kwargs: Keyword arguments to be passed to the mapper
        """
        self.map.connect(*args, **kwargs)

    def add_controller(self, name, controller):
        """ Adds a controller to the application

        Notes:
            The controller should be passed as a class, not an instance
            The name provided is used to lookup the contoller based
            on the results of a route match.  You should be sure this
            name matches the one you provided to the controller argument
            of map_connect

        Args:
            name: Name of the controller
            controller: Controller class
        """
        if isclass(controller):
            self._controllers[name] = controller
        else:
            self._controllers[name] = controller.__class__

    def on_except(self, exc, method):
        self._exc_listeners[exc] = method

    def set_session_factory(self, session_factory):
        self._session_factory = session_factory

    @staticmethod
    def add_renderer(name, serializer):
        RenderFactory.add_renderer(name, serializer)
