import json
from Distill.response import Response


class HTTPErrorResponse(Response, Exception):
    def __init__(self, status, title=None, description=None):
        super(HTTPErrorResponse, self).__init__(status)
        self.status = status
        self.title = title
        self.description = description
        self.headers['Content-Type'] = 'application/json'
        self.body = json.dumps({"title": str(self.title), "description": str(self.description)})


class HTTPMovedPermanently(HTTPErrorResponse):
    def __init__(self, location="/", title="301 Moved Permanently", description="Resource has moved"):
        super(HTTPMovedPermanently, self).__init__("301 Moved Permanently", title, description)
        self.headers['Location'] = location
        self.body = "<a href='%s'>%s</a>" % (location, location)


class HTTPMoved(HTTPErrorResponse):
    def __init__(self, location="/", title="302 Found", description="Resource has moved"):
        super(HTTPMoved, self).__init__("302 Found", title, description)
        self.headers['Location'] = location
        self.body = "<a href='%s'>%s</a>" % (location, location)


class HTTPBadRequest(HTTPErrorResponse):
    def __init__(self, title="400 Bad Request", description=None):
        super(HTTPBadRequest, self).__init__("400 Bad Request", title, description)


class HTTPUnauthorized(HTTPErrorResponse):
    def __init__(self, title="401 Unauthorized", description=None):
        super(HTTPUnauthorized, self).__init__("401 Unauthorized", title, description)


class HTTPForbidden(HTTPErrorResponse):
    def __init__(self, title="403 Forbidden", description=None):
        super(HTTPForbidden, self).__init__("403 Forbidden", title, description)


class HTTPNotFound(HTTPErrorResponse):
    def __init__(self, title="404 Not Found", description="Page not found"):
        super(HTTPNotFound, self).__init__("404 Not Found", title, description)


class HTTPNotAcceptable(HTTPErrorResponse):
    def __init__(self, title="406 Not Acceptable", description="Content not acceptable"):
        super(HTTPNotAcceptable, self).__init__("406 Not Acceptable", title, description)


class HTTPInternalServerError(HTTPErrorResponse):
    def __init__(self, title="500 Internal Server Error", description="An error has occurred processing your request"):
        super(HTTPInternalServerError, self).__init__("500 Internal Server Error", title, description)
