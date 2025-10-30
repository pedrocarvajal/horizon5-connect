from typing import Literal

from interfaces.indicator import IndicatorInterface
from services.logging import LoggingService


class MAIndicator(IndicatorInterface):
    _name: str = "Moving Average"
    _period: int
    _price_to_use: Literal["open_price", "high_price", "low_price", "close_price"]

    def __init__(self, period: int, price_to_use: str) -> None:
        self._period = period
        self._price_to_use = price_to_use

        self._log = LoggingService()
        self._log.setup("ma_indicator")
