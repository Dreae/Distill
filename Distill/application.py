import inspect
import os
import sys
from Distill import PY3
from Distill.exceptions import HTTPNotFound
from Distill.request import Request
from Distill.response import Response
from Distill.templates import template_settings


class Distill(object):
    def __init__(self, base_node=None, before=None, after=None, settings={}):
        """ INIT

        Args:
            base_node: The root of the traversal tree
            before: Method to be called before the view is called
            after: Method to be called after the view is called
            settings: Settings dictionary, will be available in all requests
            document_root: Root directory for mako templates
        """
        self.base_node = base_node
        self.settings = settings
        self._before = before
        self._after = after
        self._rsp_listeners = {a[1].distill_listens_for: a[1] for a in
                               inspect.getmembers(self.base_node,
                                                  lambda mem: hasattr(mem, "distill_listens_for"))}

        template_settings(settings)

    def __call__(self, env, start_response):
        """ Excpected WSGI method

        Creates new request using the provided env, then traverses
        the root node to the required view node
        """
        req = Request(env, self.settings)
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
                resp = res
            else:
                resp.body = str(res)
        else:
            resp = HTTPNotFound()

        if self._rsp_listeners and resp.__class__ in self._rsp_listeners:
            res = self._rsp_listeners[resp.__class__](req, resp)
            if isinstance(res, Response):
                resp = res
            else:
                resp.body = str(res)

        if self._after:
            self._after(req, resp)

        resp.finalize(env.get('wsgi.file_wrapper'))

        start_response(resp.status, resp.wsgi_headers)
        return resp.iterable

    def _traverse(self, req):
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


def response_listener(response):
    """ Decorator for listening for response types

    Notes:
        This decorator allows you to define methods that are called after view
        execution on specific response types.  Particularly usefull for defining
        custom error responses

    Args:
        response: The type of response to listen for.  Ex: HTTPNotFoundResponse
    """
    def _listen(method):
        method.distill_listens_for = response
        return method

    return _listen
