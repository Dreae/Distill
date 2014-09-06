import base64
from functools import wraps
from distill import PY3
import os
try:  # pragma: no cover
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle


class BaseSessionFactory(object):  # pragma: no cover
    """ Base session factory class

    Notes:
        This class should be overridden by any custom session factory
        you wish to create.
    """
    def __call__(self, request):
        """ Returns a new session object

        Notes:
            Calling the session factory should return a session
            class, which will then be instatiated by the framework
        """
        raise NotImplementedError('Session factory __call__ not implemented')


class BaseSession(dict):  # pragma: no cover
    """ This class stores all session data

    Notes:
        This is an abstract class.  You'll be expected
        to supply implementation for all methods on this class
    """
    def invalidate(self):
        raise NotImplementedError('Session.invalidate not implemented')

    def changed(self):
        raise NotImplementedError('Session.changed not implemented')

    def flash(self, msg, queue='', allow_duplicate=True):
        raise NotImplementedError('Session.flash not implemented')

    def pop_flash(self, queue=''):
        raise NotImplementedError('Session.pop_flash not implemented')

    def peek_flass(self, queue=''):
        raise NotImplementedError('Session.peek_flass not implemented')

    def new_csrf_token(self):
        raise NotImplementedError('Session.new_csrf_token not implemented')

    def get_csrf_token(self):
        raise NotImplementedError('Session.get_csrf_token not implemented')

    @staticmethod
    def new_ssid():
        """ Generates a new SSID """
        if PY3:  # pragma: no cover
            return base64.b32encode(os.urandom(32)).decode("ascii")
        else:
            return base64.b32encode(os.urandom(32))


def modified(func):
    @wraps(func)
    def access(session, *args, **kwargs):
        if not session.dirty:
            session.dirty = True

            def save_session(request, response):
                request.session.save(response)

            session.request.add_response_callback(save_session)
        return func(session, *args, **kwargs)

    return access


def UnencryptedLocalSessionStorage(settings):
    """ Creates a new UnencryptedLocalSession

    Notes:
        Settings is processed for session max_age and
        storage directory.  If these are not present
        in the settings, sensible defaults are used

    Args:
        settings: Current application settings dict
    """
    dir_ = './distill/sess'
    if 'distill.sessions.directory' in settings:  # pragma: no cover
        dir_ = settings['distill.sessions.directory']

    if not os.path.exists(dir_):
        os.mkdir(dir_)

    max_age = 10080
    if 'distill.sessions.max_age' in settings:  # pragma: no cover
        max_age = settings['distill.sessions.max_age']

    class UnecryptedLocalSession(BaseSession):
        _dir = dir_
        _max_age = max_age

        def __init__(self, request):
            self.request = request
            self.new = True
            self.dirty = False
            self.ssid = request.cookies.get('ssid')
            self.invalid = False
            data = {}

            if self.ssid:
                store = os.path.join(self._dir, request.cookies['ssid'])
                if not os.path.isfile(store):
                    # File has been deleted, remove cookie from request
                    del request.cookies['ssid']
                    return

                with open(store, 'rb') as fp:
                    data.update(pickle.load(fp))

            dict.__init__(self, data)

        @modified
        def changed(self):
            self.dirty = True

        @modified
        def invalidate(self):
            self.invalid = True

        get = dict.get
        __getitem__ = dict.__getitem__
        items = dict.items
        __iter__ = dict.__iter__
        values = dict.values
        keys = dict.keys
        __contains__ = dict.__contains__
        __len__ = dict.__len__

        clear = modified(dict.clear)
        update = modified(dict.update)
        setdefault = modified(dict.setdefault)
        pop = modified(dict.pop)
        popitem = modified(dict.popitem)
        __setitem__ = modified(dict.__setitem__)
        __delitem__ = modified(dict.__delitem__)

        def flash(self, msg, queue='', allow_duplicate=True):
            msgs = self.setdefault('_f_' + queue, [])
            if allow_duplicate or msg not in msgs:
                msgs.append(msg)

        def pop_flash(self, queue=''):
            return self.pop('_f_' + queue, [])

        def peek_flash(self, queue=''):
            return self.get('_f_' + queue, [])

        def new_csrf_token(self):
            token = base64.b64encode(os.urandom(32))
            self['__csrft__'] = token
            return token

        def get_csrf_token(self):
            token = self.get('__csrft__', None)
            if token is None:
                token = self.new_csrf_token()
            return token

        def save(self, response):
            """ Saves session data to a file

            Notes:
                This method serializes all data contained in the
                session object using pickle.  As such, all variables
                stored in the session should be pickleable.  It is
                not recomended to use the session to store python
                objects, instead you should store their state

            Args:
                response: The current response object
            """
            if not self.dirty:
                return

            if self.ssid is None:
                self.ssid = self.new_ssid()
                response.set_cookie('ssid', self.ssid, max_age=self._max_age)

            store = os.path.join(self._dir, self.ssid)

            if self.invalid:
                os.remove(store)
                response.set_cookie('ssid', '', max_age=0)
                return

            with open(store, 'wb+') as fp:
                pickle.dump(list(self.items()), fp, pickle.HIGHEST_PROTOCOL)

    return UnecryptedLocalSession