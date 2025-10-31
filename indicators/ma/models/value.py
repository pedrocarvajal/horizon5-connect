import datetime
from typing import Any

from pydantic import BaseModel, computed_field


class MAValueModel(BaseModel):
    _date: datetime.datetime | None = None
    _value: float = 0.0
    _: Any = None

    def to_dict(self) -> dict[str, Any]:
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
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        self._value = value
