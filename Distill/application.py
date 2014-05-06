import inspect
import sys
from Distill.exceptions import HTTPNotFound, HTTPErrorResponse
from Distill.request import Request
from Distill.response import Response
from Distill.renderers import RenderFactory


class Distill(object):
    def __init__(self, base_node=None, before=None, after=None, settings=None):
        """ INIT

        Args:
            base_node: The root of the traversal tree
            before: Method to be called before the view is called
            after: Method to be called after the view is called
            settings: Settings dictionary, will be available in all requests
            document_root: Root directory for mako templates
        """
        self.base_node = base_node
        if settings is None:
            settings = {}
        self.settings = settings
        self._before = before
        self._after = after
        self._exc_listeners = dict(
            [
                (a[1].distill_handles_exception, a[1])
                for a in inspect.getmembers(self.base_node,
                                            lambda mem: hasattr(mem, "distill_handles_exception"))
            ])

        RenderFactory.create(settings)

    def __call__(self, env, start_response):
        """ Excpected WSGI method

        Creates new request using the provided env, then traverses
        the root node to the required view node
        """
        req = Request(env, self.settings)
        resp = None
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
                resp.finalize(env.get('wsgi.file_wrapper'))
                start_response(resp.status, resp.wsgi_headers)
                return resp.iterable
            else:
                start_response(ex.status, ex.wsgi_headers, sys.exc_info())

        start_response(resp.status, resp.wsgi_headers)
        return resp.iterable

    def _request(self, env, req):
        """ Processes the request
         Notes:
            This method acts as a wrapper to easy exception handling

        Args:
            env: The wsgi environ variable
        """
        resp = Response()

        if self._before:
            self._before(req, resp)

        context = self._traverse(req)

        if context:
            if req.method == 'GET':
                res = context.on_get(req, resp)
            else:
                res = context.on_post(req, resp)
            if isinstance(res, Response):
                if isinstance(res, HTTPErrorResponse):
                    raise res
                resp = res
            else:
                resp.body = str(res)
        else:
            raise HTTPNotFound()

        if self._after:
            self._after(req, resp)

        resp.finalize(env.get('wsgi.file_wrapper'))
        return resp

    def _traverse(self, req):
        """ Traverses the application browse tree

         Notes:
            This method traverses the application tree.
            Similar to traversal in Pyramid the application
            calls __getitem__ on nodes in order, starting from
            the root.  If a node is not found in the tree, a
            HTTPNotFound is raised.  Once the application reaches
            the end of the tree it calls on_get or on_post on the
            last reached node as appropriate

        Args:
            req: The current request
        """
        p = req.path.strip("/").split("/")
        context = self.base_node
        for node in p:
            if not node:
                break
            try:
                context = context[node]
                p = p[1:]
            except (KeyError, TypeError):
                return None
        return context

    @staticmethod
    def add_renderer(name, serializer):
        RenderFactory.add_renderer(name, serializer)
