"""Strategy service base class for implementing trading strategies."""

from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from vendor.enums.command import Command
from vendor.enums.order_side import OrderSide
from vendor.enums.quality_method import QualityMethod
from vendor.enums.timeframe import Timeframe
from vendor.interfaces.analytic import AnalyticInterface
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.candle import CandleInterface
from vendor.interfaces.orderbook import OrderbookInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.interfaces.strategy import StrategyInterface
from vendor.models.backtest_expectation import BacktestExpectationModel
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.analytic import StrategyAnalytic
from vendor.services.logging import LoggingService
from vendor.services.orderbook import OrderbookService


class StrategyService(StrategyInterface):
    """
    Base service for implementing trading strategies.

    This service provides the core functionality for strategy execution, including
    order management, analytics tracking, timeframe event handling, and integration
    with the trading gateway. Strategies should inherit from this class and
    implement their specific trading logic by overriding event handlers.

    The service manages:
    - Order lifecycle through OrderbookService
    - Performance analytics through AnalyticService
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
        _orderbook: Service for managing orders and portfolio state.
        _analytic: Service for tracking performance analytics.
        _commands_queue: Queue for sending commands to external services.
        _events_queue: Queue for receiving events from external services.
        _tick: Current market tick data.
        _log: Logging service instance for logging operations.
    """

    _analytic: Optional[AnalyticInterface]
    _backtest_expectation: Optional[BacktestExpectationModel]
    _backtest_id: Optional[str]
    _backtest_quality_method: QualityMethod
    _candles: Dict[Timeframe, CandleInterface]
    _commands_queue: Optional["Queue[Command]"] = None
    _events_queue: Optional["Queue[Any]"] = None
    _leverage: int
    _portfolio: Optional[PortfolioInterface]
    _tick: Optional[TickModel]

    _log: LoggingService

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

        self._backtest = False
        self._backtest_id = None
        self._backtest_expectation = None
        self._backtest_quality_method = QualityMethod.FQS
        self._portfolio = None
        self._asset = None
        self._candles = {}
        self._orderbook = None
        self._analytic = None
        self._commands_queue = None
        self._events_queue = None
        self._tick = None

        self._id = kwargs.get("id", getattr(self, "_id", ""))
        self._name = kwargs.get("name", getattr(self, "_name", ""))
        self._allocation = kwargs.get("allocation", 0.0)
        self._leverage = kwargs.get("leverage", 1)
        self._enabled = kwargs.get("enabled", True)

    def on_end(self) -> Optional[Dict[str, Any]]:
        """
        Handle the end of strategy execution.

        In backtest mode, closes all open orders before finalizing analytics.
        Always calls the analytics service to finalize tracking and generate
        the final report.

        Returns:
            Dictionary containing the analytics report, or None.
        """
        if self._orderbook is None:
            return None

        if self._analytic is None:
            return None

        if self._backtest:
            self._log.info("Backtest mode detected, closing all orders.")

            for order in self._orderbook.orders:
                self._orderbook.close(order)

        return self._analytic.on_end()

    def on_new_day(self) -> None:
        """
        Handle a new day event.

        Called automatically when transitioning to a new day timeframe.
        Cleans up closed orders from the orderbook and updates analytics.
        """
        if self._orderbook is None:
            return

        if self._analytic is None:
            return

        if self._tick is None:
            return

        if self._asset is None:
            return

        date_str = self._tick.date.strftime("%Y-%m-%d")
        self._log.setup_prefix(f"({date_str})[{self._asset.symbol}|{self._name}]")

        self._orderbook.clean()
        self._analytic.on_new_day()

    def on_new_hour(self) -> None:
        """
        Handle a new hour event.

        Called automatically when transitioning to a new hour timeframe.
        Updates analytics for the new hour period.
        """
        if self._analytic is None:
            return

        self._analytic.on_new_hour()

    def on_new_month(self) -> None:
        """
        Handle a new month event.

        Called automatically when transitioning to a new month timeframe.
        Updates analytics for the new month period.
        """
        if self._analytic is None:
            return

        self._analytic.on_new_month()

    def on_new_week(self) -> None:
        """
        Handle a new week event.

        Called automatically when transitioning to a new week timeframe.
        Updates analytics for the new week period.
        """
        if self._analytic is None:
            return

        self._analytic.on_new_week()

    def on_tick(self, tick: TickModel) -> None:
        """
        Handle a new market tick event.

        Updates the current tick, refreshes the orderbook, updates analytics,
        and processes all candle services.

        Args:
            tick: The current market tick data.
        """
        if self._orderbook is None:
            return

        if self._analytic is None:
            return

        self._tick = tick
        self._orderbook.refresh(tick)
        self._analytic.on_tick(tick)

        for candle in self._candles.values():
            candle.on_tick(tick)

    def on_transaction(self, order: OrderModel) -> None:
        """
        Handle a transaction event (order status change).

        Called when an order's status changes. Updates analytics with the
        transaction information.

        Args:
            order: The order model representing the transaction.
        """
        if self._analytic is None:
            return

        self._analytic.on_transaction(order)

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

        if self._asset is None:
            self._log.error("Asset must be set before opening orders.")
            return

        if self._orderbook is None:
            self._log.error("Orderbook must be set before opening orders.")
            return

        order = OrderModel()
        order.strategy_id = self._id
        order.portfolio = self._portfolio
        order.asset = self._asset
        order.gateway = self._asset.gateway
        order.backtest = self._backtest
        order.backtest_id = self._backtest_id
        order.symbol = self._asset.symbol
        order.leverage = self._orderbook.leverage
        order.side = side
        order.price = price
        order.take_profit_price = take_profit_price
        order.stop_loss_price = stop_loss_price
        order.volume = volume
        order.created_at = self._tick.date
        order.updated_at = self._tick.date
        order.variables = variables

        self._orderbook.open(order)

    def setup(self, **kwargs: Any) -> None:
        """Set up the strategy with required dependencies and configuration.

        Args:
            **kwargs: Configuration parameters including:
                asset: AssetService instance managing this strategy (required).
                backtest: Whether running in backtest mode (default: False).
                backtest_id: Backtest identifier (required if backtest is True).
                portfolio: Portfolio instance (required).
                commands_queue: Queue for sending commands (required).
                events_queue: Queue for receiving events (required).
        """
        asset = kwargs.get("asset")
        backtest = kwargs.get("backtest", False)
        backtest_id = kwargs.get("backtest_id")
        portfolio = kwargs.get("portfolio")
        commands_queue = kwargs.get("commands_queue")
        events_queue = kwargs.get("events_queue")

        if asset is None:
            raise ValueError("Asset is required")

        if commands_queue is None:
            raise ValueError("Commands queue is required")

        if events_queue is None:
            raise ValueError("Events queue is required")

        if backtest and not backtest_id:
            raise ValueError("Backtest ID is required")

        if not self._id:
            raise ValueError("Strategy ID is required")

        if self._allocation <= 0:
            self._enabled = False
            return

        if self._leverage <= 0:
            raise ValueError("Leverage must be greater than 0")

        self._asset = asset
        self._backtest = backtest
        self._backtest_id = backtest_id
        self._commands_queue = commands_queue
        self._events_queue = events_queue
        self._portfolio = portfolio

        if hasattr(asset, "leverage"):
            self._leverage = asset.leverage

        self._setup_orderbook(asset)
        self._setup_analytic(asset)

        self._log.setup_prefix(f"[{asset.symbol}|{self._name}]")
        self._log.info(f"Setting up {self.name}")

    def _setup_orderbook(self, asset: AssetInterface) -> None:
        """Initialize the orderbook service."""
        self._orderbook = OrderbookService(
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            balance=self._allocation,
            allocation=self._allocation,
            leverage=self._leverage,
            gateway=asset.gateway,
            on_transaction=self.on_transaction,
        )

    def _setup_analytic(self, asset: AssetInterface) -> None:
        """Initialize the strategy analytics service."""
        if not self._orderbook:
            raise ValueError("Orderbook is required")

        self._analytic = StrategyAnalytic(
            strategy_id=self._id,
            orderbook=self._orderbook,
            backtest=self._backtest,
            backtest_id=self._backtest_id if self._backtest else None,
            quality_method=self._backtest_quality_method,
            backtest_expectation=self._backtest_expectation,
            commands_queue=self._commands_queue,
            asset_id=asset.symbol,
            portfolio_id=self._portfolio.id if self._portfolio else None,
        )

    @property
    def analytic(self) -> AnalyticInterface:
        """Return the analytic service for this strategy."""
        if self._analytic is None:
            raise RuntimeError("Analytic service not initialized. Call setup() first.")

        return self._analytic

    @property
    def asset(self) -> AssetInterface:
        """Return the asset this strategy trades."""
        if self._asset is None:
            raise RuntimeError("Asset not initialized. Call setup() first.")

        return self._asset

    @property
    def balance(self) -> float:
        """Return current cash balance."""
        if self._orderbook is None:
            return 0.0

        return self._orderbook.balance

    @property
    def exposure(self) -> float:
        """Return total market exposure."""
        if self._orderbook is None:
            return 0.0

        return self._orderbook.exposure

    @property
    def is_available_to_open_orders(self) -> bool:
        """Return whether strategy can open new orders."""
        if self._asset is None:
            return False

        return self.backtest or (self.is_live and not self._asset.is_historical_filling)

    @property
    def is_live(self) -> bool:
        """Return whether strategy is in live trading mode."""
        if self._tick is None:
            return False

        if not self._tick.is_simulated:
            return False

        return not self.backtest and not self._tick.is_simulated

    @property
    def nav(self) -> float:
        """Return net asset value."""
        if self._orderbook is None:
            return 0.0

        return self._orderbook.nav

    @property
    def orderbook(self) -> OrderbookInterface:
        """Return the orderbook managing this strategy's orders."""
        if self._orderbook is None:
            raise RuntimeError("Orderbook not initialized. Call setup() first.")

        return self._orderbook

    @property
    def orders(self) -> List[OrderModel]:
        """Return all orders for this strategy."""
        if self._orderbook is None:
            return []

        return self._orderbook.orders

    @property
    def leverage(self) -> int:
        """Return the leverage multiplier for this strategy."""
        return self._leverage
