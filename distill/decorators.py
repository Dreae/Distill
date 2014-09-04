from functools import wraps


def before(method):
    def _do(action):
        @wraps(action)
        def call(request, response):
            method(request, response)
            return action(request, response)
        return call
    return _do


def after(method):
    def _do(action):
        @wraps(action)
        def call(request, response):
            res = action(request, response)
            method(request, response)
            return res
        return call
    return _do
