try:
    import testtools as unittest
except ImportError:
    import unittest
from Distill.exceptions import *


class TestExceptions(unittest.TestCase):
    def test_init_all(self):
        notfound = HTTPNotFound()
        notacceptable = HTTPNotAcceptable()
        forbidden = HTTPForbidden()
        unauthorized = HTTPUnauthorized()
        internalservererror = HTTPInternalServerError()
        moved = HTTPMoved()
        movedpermanently = HTTPMovedPermanently()
        badrequest = HTTPBadRequest()
        base = HTTPErrorResponse("716 I am not a teapot", "This unit is not a teapot")
