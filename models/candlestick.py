import datetime
from typing import Any, Dict, Union

from pydantic import BaseModel, Field, field_validator

from configs.timezone import TIMEZONE


class CandlestickModel(BaseModel):
    source: str = ""
    symbol: str = ""
    kline_open_time: datetime.datetime = Field(default_factory=lambda: datetime.datetime.fromtimestamp(0, tz=TIMEZONE))
    open_price: float = Field(default=0.0, ge=0)
    high_price: float = Field(default=0.0, ge=0)
    low_price: float = Field(default=0.0, ge=0)
    close_price: float = Field(default=0.0, ge=0)
    volume: float = Field(default=0.0, ge=0)
    kline_close_time: datetime.datetime = Field(default_factory=lambda: datetime.datetime.fromtimestamp(0, tz=TIMEZONE))
    quote_asset_volume: float = Field(default=0.0, ge=0)
    number_of_trades: int = Field(default=0, ge=0)
    taker_buy_base_asset_volume: float = Field(default=0.0, ge=0)
    taker_buy_quote_asset_volume: float = Field(default=0.0, ge=0)

    @field_validator("kline_open_time", "kline_close_time", mode="before")
    @classmethod
    def convert_timestamp(cls, value: Union[int, float, datetime.datetime]) -> datetime.datetime:
        if isinstance(value, datetime.datetime):
            return value
        elif isinstance(value, float):
            return datetime.datetime.fromtimestamp(value, tz=TIMEZONE)
        else:
            return datetime.datetime.fromtimestamp(value / 1000, tz=TIMEZONE)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()
