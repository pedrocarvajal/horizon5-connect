import unittest

from services.gateway.helpers.has_api_error import has_api_error


class TestHasApiError(unittest.TestCase):
    def test_has_api_error_with_error_code(self) -> None:
        response = {"code": -1021, "msg": "Timestamp error"}
        has_error, msg, code = has_api_error(response)
        assert has_error is True
        assert msg == "Timestamp error"
        assert code == -1021

    def test_has_api_error_with_error_code_no_msg(self) -> None:
        response = {"code": -1021}
        has_error, msg, code = has_api_error(response)
        assert has_error is True
        assert msg == "Unknown error"
        assert code == -1021

    def test_has_api_error_without_error_code(self) -> None:
        response = {"data": "success"}
        has_error, msg, code = has_api_error(response)
        assert has_error is False
        assert msg is None
        assert code is None

    def test_has_api_error_with_none(self) -> None:
        response = None
        has_error, msg, code = has_api_error(response)
        assert has_error is False
        assert msg is None
        assert code is None

    def test_has_api_error_with_string(self) -> None:
        response = "some string"
        has_error, msg, code = has_api_error(response)
        assert has_error is False
        assert msg is None
        assert code is None

    def test_has_api_error_with_list(self) -> None:
        response = [1, 2, 3]
        has_error, msg, code = has_api_error(response)
        assert has_error is False
        assert msg is None
        assert code is None

    def test_has_api_error_with_zero_code(self) -> None:
        response = {"code": 0, "msg": "Success"}
        has_error, msg, code = has_api_error(response)
        assert has_error is True
        assert msg == "Success"
        assert code == 0

