from functools import wraps


def before(method):
    def _do(action):
        @wraps(action)
        def call(*args):
            if len(args) == 2:
                method(*args)
            else:
                method(args[1], args[2])
            return action(*args)
        return call
    return _do


def after(method):
    def _do(action):
        @wraps(action)
        def call(*args):
            res = action(*args)
            if len(args) == 2:
                method(*args)
            else:
                method(args[1], args[2])
            return res
        return call
    return _do
