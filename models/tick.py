import datetime
from typing import Any, Dict

from pydantic import BaseModel, computed_field


class TickModel(BaseModel):
    _date: datetime.datetime
    _price: float
    _: Any

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()

    @computed_field
    @property
    def date(self) -> datetime.datetime:
        return self._date

    @date.setter
    def date(self, value: datetime.datetime) -> None:
        self._date = value

    @computed_field
    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Price must be greater than 0")

        self._price = value
