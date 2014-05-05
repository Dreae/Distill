#
# &copy; 2011 Christopher Arndt, MIT License
#
import re

import time
import sys


class cached_property(object):
    '''Decorator for read-only properties evaluated only once within TTL period.

    It can be used to created a cached property like this::

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):
            # create property whose value is cached for ten minutes
            @cached_property(ttl=600)
            def randint(self):
                # will only be evaluated every 10 min. at maximum.
                return random.randint(0, 100)

    The value is cached  in the '_cache' attribute of the object instance that
    has the property getter method wrapped by this decorator. The '_cache'
    attribute value is a dictionary which has a key for every property of the
    object which is wrapped by this decorator. Each entry in the cache is
    created only when the property is accessed for the first time and is a
    two-element tuple with the last computed property value and the last time
    it was updated in seconds since the epoch.

    The default time-to-live (TTL) is 300 seconds (5 minutes). Set the TTL to
    zero for the cached value to never expire.

    To expire a cached property value manually just do::

        del instance._cache[<property name>]

    '''
    def __init__(self, ttl=300):
        self.ttl = ttl
        self.fget = None
        self.__name__ = None

    def __call__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        now = time.time()
        try:
            value, last_update = inst._cache[self.__name__]
            if 0 < self.ttl < now - last_update:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = (value, now)
        return value

_QS_RE = re.compile(r'([A-z][A-z0-9_\-\.]*)=([^&]+)')
_HEX = '0123456789abcdef'
_HEX_TO_BYTE = dict((chr(int(a + b, 16)), bytes([int(a + b, 16)])) for a in _HEX for b in _HEX)


def parse_query_string(query):
    params = {}
    for k, v in _QS_RE.findall(query):
        params[k] = url_decode(v)

    return params


def url_decode(string):
    decoded_uri = string
    if '+' in decoded_uri:
        decoded_uri = decoded_uri.replace('+', ' ')
    if '%' not in decoded_uri:
        return decoded_uri

    if sys.version_info < (3,0):
        if type(decoded_uri, str):
            decoded_uri = decoded_uri.encode('utf-8')

    tokens = decoded_uri.split('%')
    decoded_uri = tokens[0]
    for token in tokens[1:]:
        decoded_uri += _HEX_TO_BYTE[token[:2]] + token[2:]

    return decoded_uri