from functools import wraps


def exception_responder(exception):
    """ Decorator for listening for exceptions

    Notes:
        This decorator allows you to define methods that are called after the
        application catches an exception of a certain type

    Args:
        response: The type of exception to listen for.  Ex: HTTPNotFound
    """
    def _listen(method):
        method.distill_handles_exception = exception
        return method
    return _listen


def before(method):
    def _do(action):
        @wraps(action)
        def call(this, request, response):
            method(this, request, response)
            return action(this, request, response)
        return call
    return _do


def after(method):
    def _do(action):
        @wraps(action)
        def call(this, request, response):
            res = action(this, request, response)
            method(this, request, response)
            return res
        return call
    return _do
