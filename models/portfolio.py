from typing import Any

from pydantic import BaseModel, computed_field


class PortfolioModel(BaseModel):
    _initial_balance: float

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()

    @computed_field
    @property
    def initial_balance(self) -> float:
        return self._initial_balance

    @initial_balance.setter
    def initial_balance(self, value: float) -> None:
        if value < 0:
            raise ValueError("Initial balance must be greater than 0")

        self._initial_balance = value
