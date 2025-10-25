from interfaces.exchange import ExchangeInterface
from services.exchange.exchanges.binance import Binance

EXCHANGES: dict[str, type[ExchangeInterface]] = {
    "binance": Binance,
}
