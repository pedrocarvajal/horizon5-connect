from typing import Any


class GatewayInterface:
    _api_key: str
    _api_secret: str

    def __init__(self) -> None:
        pass

    def get_api_key(self) -> str:
        return self._api_key

    def open_order(self, **kwargs: Any) -> None:  # noqa: ANN401
        raise NotImplementedError
