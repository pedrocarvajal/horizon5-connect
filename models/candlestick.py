import datetime
from typing import Any, Dict, Union

from pydantic import BaseModel, computed_field

from configs.timezone import TIMEZONE


class CandlestickModel(BaseModel):
    _source: str = ""
    _symbol: str = ""
    _kline_open_time: int = 0
    _open_price: float = 0.0
    _high_price: float = 0.0
    _low_price: float = 0.0
    _close_price: float = 0.0
    _volume: float = 0.0
    _kline_close_time: int = 0
    _quote_asset_volume: float = 0.0
    _number_of_trades: int = 0
    _taker_buy_base_asset_volume: float = 0.0
    _taker_buy_quote_asset_volume: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()

    @computed_field
    @property
    def symbol(self) -> str:
        return self._symbol

    @symbol.setter
    def symbol(self, value: str) -> None:
        self._symbol = value

    @computed_field
    @property
    def source(self) -> str:
        return self._source

    @source.setter
    def source(self, value: str) -> None:
        self._source = value

    @computed_field
    @property
    def kline_open_time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            self._kline_open_time / 1000, tz=TIMEZONE
        )

    @kline_open_time.setter
    def kline_open_time(self, value: Union[int, float, datetime.datetime]) -> None:
        if isinstance(value, datetime.datetime):
            self._kline_open_time = int(value.timestamp() * 1000)
        elif isinstance(value, float):
            self._kline_open_time = int(value * 1000)
        else:
            self._kline_open_time = value

    @computed_field
    @property
    def open_price(self) -> float:
        return self._open_price

    @open_price.setter
    def open_price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Open price must be greater than 0")

        self._open_price = value

    @computed_field
    @property
    def high_price(self) -> float:
        return self._high_price

    @high_price.setter
    def high_price(self, value: float) -> None:
        if value < 0:
            raise ValueError("High price must be greater than 0")

        self._high_price = value

    @computed_field
    @property
    def low_price(self) -> float:
        return self._low_price

    @low_price.setter
    def low_price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Low price must be greater than 0")

        self._low_price = value

    @computed_field
    @property
    def close_price(self) -> float:
        return self._close_price

    @close_price.setter
    def close_price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Close price must be greater than 0")

        self._close_price = value

    @computed_field
    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        if value < 0:
            raise ValueError("Volume must be greater than 0")

        self._volume = value

    @computed_field
    @property
    def kline_close_time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            self._kline_close_time / 1000, tz=TIMEZONE
        )

    @kline_close_time.setter
    def kline_close_time(self, value: Union[int, float, datetime.datetime]) -> None:
        if isinstance(value, datetime.datetime):
            self._kline_close_time = int(value.timestamp() * 1000)
        elif isinstance(value, float):
            self._kline_close_time = int(value * 1000)
        else:
            self._kline_close_time = value

    @computed_field
    @property
    def quote_asset_volume(self) -> float:
        return self._quote_asset_volume

    @quote_asset_volume.setter
    def quote_asset_volume(self, value: float) -> None:
        if value < 0:
            raise ValueError("Quote asset volume must be greater than 0")

        self._quote_asset_volume = value

    @computed_field
    @property
    def number_of_trades(self) -> int:
        return self._number_of_trades

    @number_of_trades.setter
    def number_of_trades(self, value: int) -> None:
        if value < 0:
            raise ValueError("Number of trades must be greater than 0")

        self._number_of_trades = value

    @computed_field
    @property
    def taker_buy_base_asset_volume(self) -> float:
        return self._taker_buy_base_asset_volume

    @taker_buy_base_asset_volume.setter
    def taker_buy_base_asset_volume(self, value: float) -> None:
        if value < 0:
            raise ValueError("Taker buy base asset volume must be greater than 0")

        self._taker_buy_base_asset_volume = value

    @computed_field
    @property
    def taker_buy_quote_asset_volume(self) -> float:
        return self._taker_buy_quote_asset_volume

    @taker_buy_quote_asset_volume.setter
    def taker_buy_quote_asset_volume(self, value: float) -> None:
        if value < 0:
            raise ValueError("Taker buy quote asset volume must be greater than 0")

        self._taker_buy_quote_asset_volume = value
