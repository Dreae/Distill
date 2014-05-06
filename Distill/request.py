from Distill.helpers import cached_property, parse_query_string


class Request(object):
    def __init__(self, env, settings=None):
        """ Init
         Notes:
            Parses all relavent environ variables and stores
            them on the request

        Args:
            env: The wsgi environ variable
            settings: The application's settings dict
        """

        if settings is None:
            settings = {}
        self.settings = settings
        self.env = env

        self.stream = env['wsgi.input']
        self.errors = env['wsgi.errors']
        self.scheme = env['wsgi.url_scheme']

        path = env['PATH_INFO']
        if path:
            if len(path) != 1 and path.endswith("/"):
                self.path = path[:-1]
            else:
                self.path = path
        else:
            self.path = "/"

        if 'CONTENT_TYPE' in env:
            self.content_type = env['CONTENT_TYPE']
        elif 'HTTP_CONTENT_TYPE' in env:
            self.content_type = env['HTTP_CONTENT_TYPE']
        else:
            self.content_type = None
        if 'CONTENT_LENGTH' in env:
            self.content_length = env['CONTENT_LENGTH']
        else:
            self.content_length = None

        if 'QUERY_STRING' in env and env['QUERY_STRING']:
            self.GET = parse_query_string(env['QUERY_STRING'])
        else:
            self.GET = {}
        if self.content_type and "application/x-www-form-urlencoded" in self.content_type:
            data = self.stream.read(self.content_length)
            self.POST = parse_query_string(data)
        else:
            self.POST = {}

    @cached_property(ttl=0)
    def headers(self):
        """ Returns the HTTP headers present in the request

         Notes:
            Headers are cached permanently and should not be
            modified
        """
        headers = {}
        for k, v in self.env.items():
            if k.startswith("HTTP_"):
                headers[k[5:].replace('_', '-')] = v

        return headers

    @property
    def server(self):
        """Returns the server name, including port"""
        if 'HTTP_HOST' in self.env:
            return self.env['HTTP_HOST']
        else:
            return "{0}:{1}".format(self.env['SERVER_NAME'], self.port)

    @property
    def port(self):
        """Returns server port"""
        return self.env['SERVER_PORT']

    @property
    def location(self):
        """Returns the scripts virtual location"""
        return self.env.get('SCRIPT_NAME', '')

    @property
    def method(self):
        """Returns the request method"""
        return self.env['REQUEST_METHOD']

    def get_url(self, path):
        """ Allows you to build an arbitrary URL

         Notes:
            The returned URL will be absolute, including
            server location and scheme

        Args:
            path: The path to the required resource
        """
        return "{0}://{1}{2}{3}".format(self.scheme, self.server, self.location, path)
