import datetime
from typing import Any, Dict, Optional

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.timeframe import Timeframe
from indicators.ma import MAIndicator
from models.order import OrderModel
from models.tick import TickModel
from services.candle import CandleService
from services.logging import LoggingService
from services.strategy import StrategyService


class EMA5BreakoutStrategy(StrategyService):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _enabled = False
    _name = "EMA5Breakout"
    _settings: Dict[str, Any]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._log = LoggingService()
        self._log.setup("ema5_breakout_strategy")

        self._settings = kwargs.get(
            "settings",
            {
                "main_volume_percentage": 0.05,
                "main_take_profit_percentage": 0.03,
                "main_stop_loss_percentage": 0.15,
                "recovery_maximum_number_of_openings": 3,
                "recovery_take_profit_percentage": 0.03,
                "recovery_stop_loss_percentage": 0.15,
            },
        )

        self._previous_day_ema5_max: Optional[float] = None

        self._candles = {
            Timeframe.ONE_HOUR: CandleService(
                timeframe=Timeframe.ONE_HOUR,
                indicators=[
                    MAIndicator(
                        key="ema5",
                        period=5,
                        price_to_use="close_price",
                        exponential=True,
                    ),
                ],
            )
        }

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)
        self._tick = tick

    def on_new_hour(self) -> None:
        super().on_new_hour()
        self._check_entry_conditions()

    def on_new_day(self) -> None:
        super().on_new_day()
        assert self._tick is not None
        self._calculate_previous_day_ema5_max(self._tick)

    def on_transaction(self, order: OrderModel) -> None:
        super().on_transaction(order)

        if order.status.is_open():
            self._log.info(f"Order: {order.id}, was opened.")

        if order.status.is_closed():
            max_layers = self._settings.get("recovery_maximum_number_of_openings", 0)
            profit_percentage = order.profit_percentage * 100
            profit = order.profit

            self._log.info(f"Order: {order.id}, was closed, with profit: {profit:.2f} ({profit_percentage:.2f}%). ")

            if profit_percentage < 0 and max_layers > 0:
                self._open_recovery_order(closed_order=order)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _open_recovery_order(self, closed_order: OrderModel) -> None:
        assert self._tick is not None

        max_layers = self._settings.get("recovery_maximum_number_of_openings", 0)
        layer = closed_order.variables.get("layer", 0)
        next_layer = layer + 1
        current_price = self._tick.price
        losses = abs(closed_order.profit)
        take_profit_percentage = self._settings.get("recovery_take_profit_percentage", 0.0)
        take_profit_price = current_price + (current_price * take_profit_percentage)
        stop_loss_percentage = self._settings.get("recovery_stop_loss_percentage", 0.0)
        stop_loss_price = current_price - (current_price * stop_loss_percentage)

        volume = self._calculate_volume_based_on_target_price(
            losses=losses,
            entry_price=self._tick.price,
            take_profit_price=take_profit_price,
        )

        if next_layer > max_layers:
            self._log.warning(f"Maximum number of layers reached: {max_layers}")
            return

        self.open_order(
            OrderSide.BUY,
            current_price,
            take_profit_price,
            stop_loss_price,
            volume,
            variables={
                "layer": next_layer,
            },
        )

    def _check_entry_conditions(self) -> None:
        assert self._tick is not None

        if not self._previous_day_ema5_max:
            return

        if len(self.orderbook.where(side=OrderSide.BUY, status=OrderStatus.OPEN)) > 0:
            return

        current_price = self._tick.price
        candle_service = self._candles[Timeframe.ONE_HOUR]
        assert isinstance(candle_service, CandleService)
        candles = candle_service.candles
        current_ema5 = candles[-1]["i"]["ema5"]["value"]
        previous_ema5 = candles[-2]["i"]["ema5"]["value"]

        if previous_ema5 < self._previous_day_ema5_max and current_ema5 > self._previous_day_ema5_max:
            if self.is_live:
                self._log.info(
                    f"Breakout: {self._tick.date} | "
                    f"Opening price: {self._tick.price} | "
                    f"Previous day EMA5 max: {self._previous_day_ema5_max}"
                )

            take_profit_percentage = self._settings.get("main_take_profit_percentage", 0.0)
            stop_loss_percentage = self._settings.get("main_stop_loss_percentage", 0.0)
            take_profit_price = current_price + (current_price * take_profit_percentage)
            stop_loss_price = current_price - (current_price * stop_loss_percentage)

            # Is possible tu use self.nav, self.balance or self.allocation
            # to calculate the volume.
            volume_percentage = self._settings.get("main_volume_percentage", 0.0)
            volume = self.nav / self._tick.price
            volume = volume * volume_percentage

            self.open_order(
                OrderSide.BUY,
                self._tick.price,
                take_profit_price,
                stop_loss_price,
                volume,
                variables={
                    "layer": 0,
                },
            )

    def _calculate_previous_day_ema5_max(self, tick: TickModel) -> None:
        min_candles_required = 24
        today = tick.date.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - datetime.timedelta(days=1)
        candle_service = self._candles[Timeframe.ONE_HOUR]
        assert isinstance(candle_service, CandleService)
        candles = candle_service.candles
        ema5s = [
            candle["i"]["ema5"] for candle in candles[-min_candles_required:] if "i" in candle and "ema5" in candle["i"]
        ]

        if len(ema5s) < min_candles_required:
            self._log.warning(f"Not enough EMA5 values ({len(ema5s)}) to calculate.")
            return

        self._previous_day_ema5_max = max(
            [ema5.get("value") for ema5 in ema5s if ema5.get("date") >= yesterday and ema5.get("date") < today]
        )

    def _calculate_volume_based_on_target_price(
        self,
        losses: float,
        entry_price: float,
        take_profit_price: float,
    ) -> float:
        if take_profit_price <= entry_price:
            return 0.0

        return losses / (take_profit_price - entry_price)
