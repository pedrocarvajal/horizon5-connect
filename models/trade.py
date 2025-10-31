import datetime
from typing import Any, Dict

from pydantic import BaseModel, computed_field


class TradeModel(BaseModel):
    _id: int = 0
    _order_id: int = 0
    _symbol: str = ""
    _price: float = 0.0
    _volume: float = 0.0
    _created_at: datetime.datetime
    _updated_at: datetime.datetime
    _is_buyer: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()

    @computed_field
    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        if value < 0:
            raise ValueError("ID must be greater than or equal to 0")
        self._id = value

    @computed_field
    @property
    def order_id(self) -> int:
        return self._order_id

    @order_id.setter
    def order_id(self, value: int) -> None:
        if value < 0:
            raise ValueError("Order ID must be greater than or equal to 0")
        self._order_id = value

    @computed_field
    @property
    def symbol(self) -> str:
        return self._symbol

    @symbol.setter
    def symbol(self, value: str) -> None:
        self._symbol = value

    @computed_field
    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Price must be greater than or equal to 0")
        self._price = value

    @computed_field
    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        if value < 0:
            raise ValueError("Volume must be greater than or equal to 0")
        self._volume = value

    @computed_field
    @property
    def created_at(self) -> datetime.datetime:
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime.datetime) -> None:
        self._created_at = value

    @computed_field
    @property
    def updated_at(self) -> datetime.datetime:
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime.datetime) -> None:
        self._updated_at = value

    @computed_field
    @property
    def is_buyer(self) -> bool:
        return self._is_buyer

    @is_buyer.setter
    def is_buyer(self, value: bool) -> None:
        self._is_buyer = value
