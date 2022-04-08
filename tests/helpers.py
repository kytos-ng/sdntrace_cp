"""Module to help to create tests."""
from unittest.mock import Mock

from kytos.core import Controller
from kytos.core.config import KytosConfig


def get_controller_mock():
    """Return a controller mock."""
    options = KytosConfig().options["daemon"]
    controller = Controller(options)
    controller.log = Mock()
    return controller


def get_mocked_requests(_):
    """Mock requests.get."""
    return MockResponse(
        {
        },
        200,
    )


class MockResponse:
    """
    Mock a requests response object.

    Just define a function and add the patch decorator to the test.
    Example:
    def mocked_requests_get(*args, **kwargs):
        return MockResponse({}, 200)
    @patch('requests.get', side_effect=mocked_requests_get)

    """

    def __init__(self, json_data, status_code):
        """Create mock response object with parameters.

        Args:
            json_data: JSON response content
            status_code: HTTP status code.
        """
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        """Return the response json data."""
        return self.json_data

    def __str__(self):
        return self.__class__.__name__
