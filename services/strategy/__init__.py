# Code reviewed on 2025-11-20 by Pedro Carvajal

import datetime
from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from enums.order_side import OrderSide
from enums.timeframe import Timeframe
from interfaces.analytic import AnalyticInterface
from interfaces.candle import CandleInterface
from interfaces.portfolio import PortfolioInterface
from interfaces.strategy import StrategyInterface
from models.order import OrderModel
from models.tick import TickModel
from services.analytic import AnalyticService
from services.asset import AssetService
from services.logging import LoggingService

from .handlers.orderbook import OrderbookHandler
from .helpers.get_truncated_timeframe import get_truncated_timeframe


class StrategyService(StrategyInterface):
    """
    Base service for implementing trading strategies.

    This service provides the core functionality for strategy execution, including
    order management, analytics tracking, timeframe event handling, and integration
    with the trading gateway. Strategies should inherit from this class and
    implement their specific trading logic by overriding event handlers.

    The service manages:
    - Order lifecycle through OrderbookHandler
    - Performance analytics through AnalyticService
    - Timeframe transitions (minute, hour, day, week, month)
    - Order creation and management
    - Integration with asset and gateway services

    Attributes:
        _id: Unique identifier for the strategy.
        _name: Name of the strategy (typically set by child classes).
        _enabled: Whether the strategy is enabled for execution.
        _backtest: Whether running in backtest mode.
        _backtest_id: Optional backtest identifier.
        _asset: Reference to the asset service managing this strategy.
        _allocation: Capital allocation for this strategy.
        _leverage: Leverage multiplier for trading.
        _candles: Dictionary of candle services by timeframe.
        _orderbook: Handler for managing orders and portfolio state.
        _analytic: Service for tracking performance analytics.
        _commands_queue: Queue for sending commands to external services.
        _events_queue: Queue for receiving events from external services.
        _last_timestamps: Dictionary tracking last timestamp for each timeframe.
        _tick: Current market tick data.
        _log: Logging service instance for logging operations.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _id: str
    _name: str
    _enabled: bool

    _backtest: bool
    _backtest_id: Optional[str]
    _portfolio: Optional[PortfolioInterface]
    _asset: Optional[AssetService]
    _allocation: float
    _leverage: int
    _candles: Dict[Timeframe, CandleInterface]

    _orderbook: Optional[OrderbookHandler]
    _analytic: Optional[AnalyticInterface]

    _commands_queue: Optional[Queue]
    _events_queue: Optional[Queue]

    _last_timestamps: Dict[Timeframe, datetime.datetime]
    _tick: Optional[TickModel]
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the strategy service.

        Args:
            **kwargs: Additional keyword arguments:
                id: Unique identifier for the strategy.
                name: Name of the strategy (default: empty string).
                allocation: Capital allocation for this strategy (default: 0.0).
                leverage: Leverage multiplier for trading (default: 1).
                enabled: Whether the strategy is enabled (default: True).
        """
        self._log = LoggingService()
        self._log.setup("strategy_service")

        self._backtest = False
        self._backtest_id = None
        self._portfolio = None
        self._asset = None
        self._candles = {}
        self._orderbook = None
        self._analytic = None
        self._commands_queue = None
        self._events_queue = None
        self._last_timestamps = {}
        self._tick = None

        self._id = kwargs.get("id")
        self._name = kwargs.get("name", "")
        self._allocation = kwargs.get("allocation", 0.0)
        self._leverage = kwargs.get("leverage", 1)
        self._enabled = kwargs.get("enabled", True)

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setup(self, **kwargs: Any) -> None:
        """
        Set up the strategy with required dependencies and configuration.

        Initializes the orderbook handler and analytics service, and validates
        all required parameters. This method must be called before the strategy
        can be used.

        Args:
            **kwargs: Configuration parameters:
                asset: AssetService instance managing this strategy (required).
                backtest: Whether running in backtest mode (default: False).
                backtest_id: Backtest identifier (required if backtest is True).
                commands_queue: Queue for sending commands (required).
                events_queue: Queue for receiving events (required).

        Raises:
            ValueError: If any required parameter is missing or invalid.
        """
        self._asset = kwargs.get("asset")
        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")
        self._portfolio = kwargs.get("portfolio")
        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")

        self._validate_setup_parameters()

        self._orderbook = OrderbookHandler(
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            balance=self._allocation,
            allocation=self._allocation,
            leverage=self._leverage,
            gateway=self.asset.gateway,
            on_transaction=self.on_transaction,
        )

        self._analytic = AnalyticService(
            strategy_id=self._id,
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            orderbook=self._orderbook,
            commands_queue=self._commands_queue,
            events_queue=self._events_queue,
        )

        self._log.info(f"Setting up {self.name}")

    def on_tick(self, tick: TickModel) -> None:
        """
        Handle a new market tick event.

        Updates the current tick, checks for timeframe transitions, refreshes
        the orderbook, updates analytics, and processes all candle services.

        Args:
            tick: The current market tick data.
        """
        self._tick = tick
        self._check_timeframe_transitions(tick)
        self._orderbook.refresh(tick)
        self._analytic.on_tick(tick)

        for candle in self._candles.values():
            candle.on_tick(tick)

    def on_new_hour(self) -> None:
        """
        Handle a new hour event.

        Called automatically when transitioning to a new hour timeframe.
        Updates analytics for the new hour period.
        """
        self._analytic.on_new_hour()

    def on_new_day(self) -> None:
        """
        Handle a new day event.

        Called automatically when transitioning to a new day timeframe.
        Cleans up closed orders from the orderbook and updates analytics.
        """
        self._orderbook.clean()
        self._analytic.on_new_day()

    def on_new_week(self) -> None:
        """
        Handle a new week event.

        Called automatically when transitioning to a new week timeframe.
        Updates analytics for the new week period.
        """
        self._analytic.on_new_week()

    def on_new_month(self) -> None:
        """
        Handle a new month event.

        Called automatically when transitioning to a new month timeframe.
        Updates analytics for the new month period.
        """
        self._analytic.on_new_month()

    def on_transaction(self, order: OrderModel) -> None:
        """
        Handle a transaction event (order status change).

        Called when an order's status changes. Updates analytics with the
        transaction information.

        Args:
            order: The order model representing the transaction.
        """
        self._analytic.on_transaction(order)

    def on_end(self) -> None:
        """
        Handle the end of strategy execution.

        In backtest mode, closes all open orders before finalizing analytics.
        Always calls the analytics service to finalize tracking and generate
        the final report.
        """
        if self._backtest:
            self._log.info("Backtest mode detected, closing all orders.")

            for order in self._orderbook.orders:
                self._orderbook.close(order)

        self._analytic.on_end()

    def open_order(
        self,
        side: OrderSide,
        price: float,
        take_profit_price: float,
        stop_loss_price: float,
        volume: float,
        variables: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Open a new trading order.

        Creates and submits a new order with the specified parameters. The order
        will only be opened if the strategy is available to open orders (not
        blocked by historical filling or live mode restrictions).

        Args:
            side: Order direction (BUY or SELL).
            price: Entry price for the order.
            take_profit_price: Target price for profit taking.
            stop_loss_price: Stop loss price for risk management.
            volume: Order volume/quantity.
            variables: Optional dictionary of custom variables to attach to the order.

        Note:
            Orders are only opened if `is_available_to_open_orders` returns True.
            In backtest mode, orders are always allowed. In live mode, orders are
            blocked during historical data filling.
        """
        if variables is None:
            variables = {}

        if not self.is_available_to_open_orders:
            return

        if self._tick is None:
            self._log.error("Tick must be set before opening orders.")
            return

        order = OrderModel()
        order.strategy_id = self._id
        order.portfolio = self._portfolio
        order.asset = self.asset
        order.gateway = self.asset.gateway
        order.backtest = self._backtest
        order.backtest_id = self._backtest_id
        order.symbol = self.asset.symbol
        order.side = side
        order.price = price
        order.take_profit_price = take_profit_price
        order.stop_loss_price = stop_loss_price
        order.volume = volume
        order.created_at = self._tick.date
        order.updated_at = self._tick.date
        order.variables = variables

        self.orderbook.open(order)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_setup_parameters(self) -> None:
        """
        Validate all required setup parameters.

        Raises:
            ValueError: If any required parameter is missing or invalid.
        """
        if self._asset is None:
            raise ValueError("Asset is required")

        if self._allocation <= 0:
            raise ValueError("Allocation must be greater than 0")

        if self._backtest and self._backtest_id is None:
            raise ValueError("Backtest ID is required")

        if self._commands_queue is None:
            raise ValueError("Commands queue is required")

        if self._events_queue is None:
            raise ValueError("Events queue is required")

        if not self._id:
            raise ValueError("Strategy ID is required")

        if self._leverage <= 0:
            raise ValueError("Leverage must be greater than 0")

    def _check_timeframe_transitions(self, tick: TickModel) -> None:
        """
        Check for timeframe transitions and trigger appropriate events.

        Compares the current tick's timestamp with the last recorded timestamp
        for each timeframe. If a new period is detected, triggers the corresponding
        event handler (on_new_minute, on_new_hour, etc.).

        Args:
            tick: The current market tick data.
        """
        current_time = tick.date

        for timeframe in Timeframe:
            last_timestamp = self._last_timestamps.get(timeframe)

            if last_timestamp is None:
                self._last_timestamps[timeframe] = get_truncated_timeframe(current_time, timeframe)
                continue

            current_period = get_truncated_timeframe(current_time, timeframe)

            if current_period > last_timestamp:
                self._last_timestamps[timeframe] = current_period
                self._trigger_timeframe_event(timeframe)

    def _trigger_timeframe_event(self, timeframe: Timeframe) -> None:
        """
        Trigger the appropriate event handler for a timeframe transition.

        Args:
            timeframe: The timeframe that has transitioned to a new period.
        """
        if timeframe == Timeframe.ONE_MINUTE:
            self.on_new_minute()

        elif timeframe == Timeframe.ONE_HOUR:
            self.on_new_hour()

        elif timeframe == Timeframe.ONE_DAY:
            self.on_new_day()

        elif timeframe == Timeframe.ONE_WEEK:
            self.on_new_week()

        elif timeframe == Timeframe.ONE_MONTH:
            self.on_new_month()

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def id(self) -> str:
        return self._id

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def name(self) -> str:
        return self._name

    @property
    def backtest(self) -> bool:
        return self._backtest

    @property
    def asset(self) -> AssetService:
        return self._asset

    @property
    def orderbook(self) -> OrderbookHandler:
        return self._orderbook

    @property
    def allocation(self) -> float:
        return self._orderbook.allocation

    @property
    def nav(self) -> float:
        return self._orderbook.nav

    @property
    def exposure(self) -> float:
        return self._orderbook.exposure

    @property
    def balance(self) -> float:
        return self._orderbook.balance

    @property
    def orders(self) -> List[OrderModel]:
        return self._orderbook.orders

    @property
    def is_live(self) -> bool:
        return not self.backtest and self._tick is not None and not self._tick.is_simulated

    @property
    def is_available_to_open_orders(self) -> bool:
        return self.backtest or (self.is_live and not self.asset.is_historical_filling)
