import datetime
from typing import Any

from pydantic import BaseModel, computed_field


class Candlestick(BaseModel):
    _kline_open_time: int
    _open_price: float
    _high_price: float
    _low_price: float
    _close_price: float
    _volume: float
    _kline_close_time: int
    _quote_asset_volume: float
    _number_of_trades: int
    _taker_buy_base_asset_volume: float
    _taker_buy_quote_asset_volume: float

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()

    @computed_field
    @property
    def kline_open_time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            self._kline_open_time / 1000, tz=datetime.UTC
        )

    @kline_open_time.setter
    def kline_open_time(self, value: int) -> None:
        self._kline_open_time = value

    @computed_field
    @property
    def open_price(self) -> float:
        return self._open_price

    @open_price.setter
    def open_price(self, value: float) -> None:
        self._open_price = value

    @computed_field
    @property
    def high_price(self) -> float:
        return self._high_price

    @high_price.setter
    def high_price(self, value: float) -> None:
        self._high_price = value

    @computed_field
    @property
    def low_price(self) -> float:
        return self._low_price

    @low_price.setter
    def low_price(self, value: float) -> None:
        self._low_price = value

    @computed_field
    @property
    def close_price(self) -> float:
        return self._close_price

    @close_price.setter
    def close_price(self, value: float) -> None:
        self._close_price = value

    @computed_field
    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = value

    @computed_field
    @property
    def kline_close_time(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            self._kline_close_time / 1000, tz=datetime.UTC
        )

    @kline_close_time.setter
    def kline_close_time(self, value: int) -> None:
        self._kline_close_time = value

    @computed_field
    @property
    def quote_asset_volume(self) -> float:
        return self._quote_asset_volume

    @quote_asset_volume.setter
    def quote_asset_volume(self, value: float) -> None:
        self._quote_asset_volume = value

    @computed_field
    @property
    def number_of_trades(self) -> int:
        return self._number_of_trades

    @number_of_trades.setter
    def number_of_trades(self, value: int) -> None:
        self._number_of_trades = value

    @computed_field
    @property
    def taker_buy_base_asset_volume(self) -> float:
        return self._taker_buy_base_asset_volume

    @taker_buy_base_asset_volume.setter
    def taker_buy_base_asset_volume(self, value: float) -> None:
        self._taker_buy_base_asset_volume = value

    @computed_field
    @property
    def taker_buy_quote_asset_volume(self) -> float:
        return self._taker_buy_quote_asset_volume

    @taker_buy_quote_asset_volume.setter
    def taker_buy_quote_asset_volume(self, value: float) -> None:
        self._taker_buy_quote_asset_volume = value
