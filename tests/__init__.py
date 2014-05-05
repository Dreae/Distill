from unittest import TestSuite
from tests import test_request
from tests import test_response
from tests import test_exceptions
from tests import test_renderers
from tests import test_application

test_suite = TestSuite()
test_suite.addTest(test_request.suite())
test_suite.addTest(test_response.suite())
test_suite.addTest(test_exceptions.suite())
test_suite.addTest(test_renderers.suite())
test_suite.addTest(test_application.suite())