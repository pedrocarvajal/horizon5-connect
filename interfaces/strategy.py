from typing import Any

from models.order import OrderModel
from models.tick import TickModel


class StrategyInterface:
    def setup(self, **kwargs: Any) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_new_minute(self, tick: TickModel) -> None:
        pass

    def on_new_hour(self, tick: TickModel) -> None:
        pass

    def on_new_day(self, tick: TickModel) -> None:
        pass

    def on_new_week(self, tick: TickModel) -> None:
        pass

    def on_new_month(self, tick: TickModel) -> None:
        pass

    def on_transaction(self, order: OrderModel) -> None:
        pass

    def on_end(self) -> None:
        pass
