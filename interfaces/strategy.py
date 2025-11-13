from abc import ABC, abstractmethod
from typing import Any

from models.order import OrderModel
from models.tick import TickModel


class StrategyInterface(ABC):
    @abstractmethod
    def setup(self, **kwargs: Any) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:  # noqa: B027
        pass

    def on_new_minute(self) -> None:  # noqa: B027
        pass

    def on_new_hour(self) -> None:  # noqa: B027
        pass

    def on_new_day(self) -> None:  # noqa: B027
        pass

    def on_new_week(self) -> None:  # noqa: B027
        pass

    def on_new_month(self) -> None:  # noqa: B027
        pass

    def on_transaction(self, order: OrderModel) -> None:  # noqa: B027
        pass

    def on_end(self) -> None:  # noqa: B027
        pass
