import unittest

from services.gateway.helpers.has_api_error import has_api_error


class TestHasApiError(unittest.TestCase):
    _ERROR_CODE_TIMESTAMP: int = -1021
    _ERROR_CODE_ZERO: int = 0
    _ERROR_MSG_TIMESTAMP: str = 'Timestamp error'
    _ERROR_MSG_SUCCESS: str = 'Success'
    _ERROR_MSG_UNKNOWN: str = 'Unknown error'

    def test_has_api_error_with_error_code_and_message(self) -> None:
        response = {'code': self._ERROR_CODE_TIMESTAMP, 'msg': self._ERROR_MSG_TIMESTAMP}
        has_error, msg, code = has_api_error(response)
        assert has_error is True
        assert msg == self._ERROR_MSG_TIMESTAMP
        assert code == self._ERROR_CODE_TIMESTAMP

    def test_has_api_error_with_error_code_no_message(self) -> None:
        response = {'code': self._ERROR_CODE_TIMESTAMP}
        has_error, msg, code = has_api_error(response)
        assert has_error is True
        assert msg == self._ERROR_MSG_UNKNOWN
        assert code == self._ERROR_CODE_TIMESTAMP

    def test_has_api_error_with_zero_code(self) -> None:
        response = {'code': self._ERROR_CODE_ZERO, 'msg': self._ERROR_MSG_SUCCESS}
        has_error, msg, code = has_api_error(response)
        assert has_error is True
        assert msg == self._ERROR_MSG_SUCCESS
        assert code == self._ERROR_CODE_ZERO

    def test_has_api_error_without_error_code(self) -> None:
        response = {'data': 'success'}
        has_error, msg, code = has_api_error(response)
        assert has_error is False
        assert msg is None
        assert code is None

    def test_has_api_error_with_none_response(self) -> None:
        response = None
        has_error, msg, code = has_api_error(response)
        assert has_error is False
        assert msg is None
        assert code is None

    def test_has_api_error_with_string_response(self) -> None:
        response = 'some string'
        has_error, msg, code = has_api_error(response)
        assert has_error is False
        assert msg is None
        assert code is None

    def test_has_api_error_with_list_response(self) -> None:
        response = [1, 2, 3]
        has_error, msg, code = has_api_error(response)
        assert has_error is False
        assert msg is None
        assert code is None
