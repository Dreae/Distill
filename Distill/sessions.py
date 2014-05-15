import base64
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
    def load(self, request):
        """ Loads the session for the given request

         Note:
            This method is implementation dependent. It should load
            the session data as appropriate, using the session cookie
            and initialize the session on the request

         Args:
            request: the request for which the session should be loaded
        """
        raise NotImplementedError()

    def save(self, request, response):
        """ Saves the request's session

        Notes:
            This method should save the session to the underlying storage
            engine.  This method should only save the session data if
            request.session.changed == True, otherwise you will be
            wasting resources.  Response is given so that any Set-Cookie
            headers can be set as needed.

        Args:
            request: The requests whos session should be saved
            response: The current response object
        """
        raise NotImplementedError()

    @staticmethod
    def new_ssid():
        """ Generates a new SSID """
        return str(base64.b32encode(os.urandom(32)))


class Session(dict):
    """ This class stores all session data

    Notes:
        This class is a subclass of dict so that it can
        implement the necessary tracking of changes.
        Keep in mind, should you change any mutable variable
        stored in the session, such as a dict or list, you
        should manually call session.modified(), as simply
        using session['dict']['key'] = value does not trigger
        the changed flag
    """
    def __init__(self, data=None, **kwargs):
        if data is None:
            data = {}

        self._dict = dict()
        self.changed = False
        self.invalid = False
        self._dict.update(data, **kwargs)

    def __getitem__(self, item):
        return self._dict[item]

    def __setitem__(self, key, value):
        self._dict[key] = value
        self.changed = True

    def __delitem__(self, key):
        del self._dict[key]
        self.changed = True

    def __contains__(self, item):
        return item in self._dict

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()

    def update(self, E=None, **F):
        self._dict.update(E, **F)
        self.changed = True

    def clear(self):
        self.changed = True
        self._dict.clear()

    def items(self):
        return self._dict.items()

    def keys(self):
        return self._dict.keys()

    def get(self, k, d=None):
        return self._dict.get(k, d)

    def setdefault(self, k, d=None):
        if not k in self._dict:
            self[k] = d
            self.changed = True

    def invalidate(self):
        self.invalid = True
        self.clear()

    def modified(self):
        self.changed = True


class UnencryptedLocalSessionStorage(BaseSessionFactory):
    """ UnencryptedLocalSessionStorage

    Notes:
        This session factory stores sessions unencrypted
        on the disk using python's pickle module. Suitable
        if you do not store sensitive information in the
        session
    """
    def __init__(self, settings):
        """ Init

        Notes:
            Settings is processed for session max_age and
            storage directory.  If these are not present
            in the settings, sensible defaults are used

        Args:
            settings: Current application settings dict
        """
        if 'distill.sessions.directory' in settings:  # pragma: no cover
            self.dir = settings['distill.sessions.directory']
        else:  # pragma: no cover
            self.dir = './distill/sess'

        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        if 'distill.sessions.max_age' in settings:  # pragma: no cover
            self.max_age = settings['distill.sessions.max_age']
        else:  # pragma: no cover
            self.max_age = 10080

    def load(self, request):
        """ Loads the Sesssion data from a file using pickle

        Notes:
            This method loads the session data from the file.
            The session data should be a dict that has been
            serialized using the pickle module

        Args:
            request: The request object who's session to load
        """
        if not 'ssid' in request.cookies:
            return
        store = os.path.join(self.dir, request.cookies['ssid'])
        if not os.path.isfile(store):
            # File has been deleted, remove cookie from request
            del request.cookies['ssid']
            return

        with open(store, 'rb') as fp:
            request.session = Session(pickle.load(fp))

    def save(self, request, response):
        """ Saves session data to a file

        Notes:
            This method serializes all data contained in the
            session object using pickle.  As such, all variables
            stored in the session should be pickleable.  It is
            not recomended to use the session to store python
            objects, instead you should store their state

        Args:
            request: The request who's session to save
            response: The current response object
        """
        if not request.session.changed:
            return

        if not 'ssid' in request.cookies:
            ssid = self.new_ssid()
            response.set_cookie('ssid', ssid, max_age=self.max_age)
        else:
            ssid = request.cookies['ssid']

        store = os.path.join(self.dir, ssid)

        if request.session.invalid:
            os.remove(store)
            response.set_cookie('ssid', '', max_age=0)
            return

        with open(store, 'wb+') as fp:
            pickle.dump(list(request.session.items()), fp, pickle.HIGHEST_PROTOCOL)