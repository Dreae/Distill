from functools import wraps


def before(method):
    def _do(action):
        @wraps(action)
        def call(*args):
            method(*args)
            return action(*args)
        return call
    return _do


def after(method):
    def _do(action):
        @wraps(action)
        def call(*args):
            res = action(*args)
            method(*args)
            return res
        return call
    return _do
