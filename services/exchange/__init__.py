from configs.exchanges import EXCHANGES
from interfaces.exchange import ExchangeInterface


class ExchangeService(ExchangeInterface):
    _exchange_name: str
    _exchange_credentials: dict[str, str]
    _exchange: ExchangeInterface

    def __init__(self, exchange: str, credentials: dict[str, str]) -> None:
        self._exchanges = EXCHANGES
        self._exchange_name = exchange
        self._exchange_credentials = credentials

        self._setup()

    def _setup(self) -> None:
        if self._exchange_name not in self._exchanges:
            raise ValueError(f"Exchange {self._exchange_name} not found")

        self._exchange = self._exchanges[self._exchange_name](
            self._exchange_credentials
        )
