#
# &copy; 2011 Christopher Arndt, MIT License
#
import re
import time
from distill import PY2


class cached_property(object):  # pragma: no cover
    """Decorator for read-only properties evaluated only once within TTL period.

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

    """
    def __init__(self):
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
            value = inst._cache[self.__name__]
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = value
        return value

_QS_RE = re.compile(r'([A-z][A-z0-9_\-\.]*)=([^&]+)')
_HEX = '0123456789abcdef'
_HEX_TO_BYTE = dict((a + b, chr(int(a + b, 16))) for a in _HEX for b in _HEX)
_BYTE_TO_HEX = dict((int(a + b, 16), a + b) for a in _HEX for b in _HEX)
ALLOWED_CHRS = 'abcdefghijklmnopqrstuvwxyz'
ALLOWED_CHRS += ALLOWED_CHRS.upper()
ALLOWED_CHRS += '0123456789'


def parse_query_string(query):
    """Parses an HTTP query string into a dict"""
    params = {}
    for k, v in _QS_RE.findall(query):
        params[k] = url_decode(v)

    return params


def url_decode(string):
    """ Decodes the URL encoded string

     Notes:
        This function runs considerablly faster than
        the one provided in urllib.  The returned string
        will include any unicode bytes in the string as if
        the user had used string.encode('utf-8')

    Args:
        string: The string to be decoded
    """
    decoded_uri = string
    if '+' in decoded_uri:
        decoded_uri = decoded_uri.replace('+', ' ')
    if '%' not in decoded_uri:
        return decoded_uri

    if PY2:  # pragma: no cover
        if type(decoded_uri) == str:
            decoded_uri = decoded_uri.encode('utf-8')

    tokens = decoded_uri.split('%')
    decoded_uri = tokens[0]
    for token in tokens[1:]:
        decoded_uri += _HEX_TO_BYTE[token[:2].lower()] + token[2:]

    return decoded_uri


class CaseInsensitiveDict(dict):
    """ A case-insensitive dict object

    Notes:
        Used by Request object for headers, since WSGI
        scraps header capitalization.  This allows developers
        with OCD to access the header dict using any
        capitilization they like
    """

    def __init__(self, data=None, **kwargs):
        self._dict = dict()
        if data is None:
            data = {}
        self._dict.update(data, **kwargs)

    def __setitem__(self, key, value):
        self._dict[key.lower()] = (key, value)

    def __getitem__(self, item):
        return self._dict[item.lower()][1]

    def __delitem__(self, key):
        del self._dict[key.lower()]

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return (k for k, v in self._dict.values())

    def keys(self):
        return [k for k, v in self._dict.values()]

    def get(self, k, d=None):
        try:
            return self._dict[k.lower()][1]
        except KeyError:
            return d

    def setdefault(self, k, d=None):
        if not k.lower() in self._dict:
            self._dict[k.lower()] = (k, d)

    def iteritems(self):
        return self._dict.values()

    def items(self):
        return self._dict.values()

    def copy(self):
        return CaseInsensitiveDict(self._dict)

    def __contains__(self, item):
        return item.lower() in self._dict