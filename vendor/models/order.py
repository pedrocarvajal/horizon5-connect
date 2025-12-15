"""Order model for trading operations with lifecycle management."""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from vendor.configs.system import SYSTEM_PREFIX
from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.enums.order_type import OrderType
from vendor.helpers.get_slug import get_slug
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.models.tick import TickModel
from vendor.services.gateway.models.gateway_trade import GatewayTradeModel
from vendor.services.logging import LoggingService


class OrderModel(BaseModel):
    """Trading order with status tracking, profit calculation, and gateway integration.

    Attributes:
        id: Unique order identifier.
        gateway_order_id: Exchange-specific order ID.
        backtest: Whether order is from backtest.
        portfolio: Associated portfolio instance.
        asset: Associated asset instance.
        side: Order side (BUY/SELL).
        status: Current order status.
        volume: Order size.
        price: Entry price.
        take_profit_price: Take profit target.
        stop_loss_price: Stop loss threshold.
        trades: List of executed trades.
        logs: Order event history.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gateway_order_id: Optional[str] = None
    backtest: bool = False
    backtest_id: Optional[str] = None
    portfolio: Optional[PortfolioInterface] = None
    asset: Optional[AssetInterface] = None
    strategy_id: Optional[str] = None
    symbol: str = ""
    gateway: Any = None
    side: Optional[OrderSide] = None
    order_type: Optional[OrderType] = Field(default=OrderType.MARKET)
    status: OrderStatus = Field(default=OrderStatus.OPENING)
    volume: float = Field(default=0.0, ge=0)
    executed_volume: float = Field(default=0.0, ge=0)
    price: float = Field(default=0.0, ge=0)
    close_price: float = Field(default=0.0, ge=0)
    take_profit_price: float = Field(default=0.0, ge=0)
    stop_loss_price: float = Field(default=0.0, ge=0)

    leverage: int = Field(default=1, ge=1)
    commission: float = Field(default=0.0, ge=0)
    commission_percentage: float = Field(default=0.0, ge=0)

    trades: List[GatewayTradeModel] = Field(default_factory=lambda: [])
    logs: List[Dict[str, Any]] = Field(default_factory=lambda: [])
    variables: Dict[str, Any] = Field(default_factory=dict)

    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize order model and setup logging.

        Args:
            **kwargs: Order attributes.
        """
        super().__init__(**kwargs)

        self._log = LoggingService()
        self._log.setup_prefix(f"[{self.id}]")

    def __setattr__(self, name: str, value: Any) -> None:
        """Track status changes when setting attributes.

        Args:
            name: Attribute name.
            value: Attribute value.
        """
        if name == "status" and hasattr(self, "status"):
            self._track_status_change(value)

        super().__setattr__(name, value)

    def check_if_ready_to_close_take_profit(self, tick: TickModel) -> bool:
        """Check if order should close at take profit.

        Args:
            tick: Current market tick.

        Returns:
            True if TP conditions met.
        """
        return self.status.is_open() and self.take_profit_price > 0 and tick.close_price >= self.take_profit_price

    def check_if_ready_to_close_stop_loss(self, tick: TickModel) -> bool:
        """Check if order should close at stop loss.

        Args:
            tick: Current market tick.

        Returns:
            True if SL conditions met.
        """
        return self.status.is_open() and self.stop_loss_price > 0 and tick.close_price <= self.stop_loss_price

    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary representation.

        Returns:
            Dictionary with all order fields.
        """
        gateway = self.gateway.name if self.gateway else None
        side = self.side.value if self.side else None
        order_type = self.order_type.value if self.order_type else None

        return {
            "id": self.id,
            "gateway_order_id": self.gateway_order_id,
            "backtest": self.backtest,
            "backtest_id": self.backtest_id,
            "portfolio_id": self.portfolio_id,
            "asset_id": self.asset_id,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "gateway": gateway,
            "side": side,
            "order_type": order_type,
            "status": self.status.value,
            "volume": self.volume,
            "executed_volume": self.executed_volume,
            "price": self.price,
            "close_price": self.close_price,
            "take_profit_price": self.take_profit_price,
            "stop_loss_price": self.stop_loss_price,
            "client_order_id": self.client_order_id,
            "filled": self.filled,
            "profit": self.profit,
            "profit_percentage": self.profit_percentage,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert order to API-compatible dictionary format.

        Returns:
            Dictionary structured for Horizon Router API with strategy_id,
            asset_id, portfolio_id at root level and order details in data field.
        """
        gateway = self.gateway.name if self.gateway else None
        side = self.side.value if self.side else None
        order_type = self.order_type.value if self.order_type else None
        created_at = self.created_at.isoformat() if self.created_at else None
        updated_at = self.updated_at.isoformat() if self.updated_at else None

        return {
            "strategy_id": self.strategy_id,
            "asset_id": self.asset_id,
            "portfolio_id": self.portfolio_id,
            "backtest_id": self.backtest_id,
            "backtest": self.backtest,
            "data": {
                "id": self.id,
                "gateway_order_id": self.gateway_order_id,
                "symbol": self.symbol,
                "gateway": gateway,
                "side": side,
                "order_type": order_type,
                "status": self.status.value,
                "volume": self.volume,
                "executed_volume": self.executed_volume,
                "price": self.price,
                "close_price": self.close_price,
                "take_profit_price": self.take_profit_price,
                "stop_loss_price": self.stop_loss_price,
                "commission": self.commission,
                "commission_percentage": self.commission_percentage,
                "client_order_id": self.client_order_id,
                "filled": self.filled,
                "profit": self.profit,
                "profit_percentage": self.profit_percentage,
                "created_at": created_at,
                "updated_at": updated_at,
            },
        }

    def _track_status_change(self, status: OrderStatus) -> None:
        self.logs.append(
            {
                "event": "status_change",
                "status": status.value,
            }
        )

    @computed_field
    @property
    def portfolio_id(self) -> Optional[str]:
        """Get portfolio ID from associated portfolio."""
        return self.portfolio.id if self.portfolio else None

    @computed_field
    @property
    def asset_id(self) -> Optional[str]:
        """Get asset symbol from associated asset."""
        return self.asset.symbol if self.asset else None

    @computed_field
    @property
    def client_order_id(self) -> str:
        """Generate exchange-compatible client order ID."""
        max_length = 16
        max_length_for_system_prefix = 4

        id_suffix = self.id.split("-")[-1]
        client_order_id = get_slug(f"{SYSTEM_PREFIX}-{id_suffix}")[:16].lower()

        if len(SYSTEM_PREFIX) > max_length_for_system_prefix:
            raise ValueError("System prefix must be less than 4 characters.")

        if len(client_order_id) > max_length:
            raise ValueError("Client order ID must be less than 16 characters.")

        return client_order_id

    @computed_field
    @property
    def filled(self) -> bool:
        """Check if order volume is fully executed."""
        return self.volume > 0 and self.executed_volume >= self.volume

    @computed_field
    @property
    def profit(self) -> float:
        """Calculate profit in absolute currency units."""
        if self.side is not None and self.side.is_sell():
            return (self.price - self.close_price) * self.volume

        return (self.close_price - self.price) * self.volume

    @computed_field
    @property
    def profit_percentage(self) -> float:
        """Calculate profit as percentage of account allocation.

        This represents the impact of the trade on the overall account.
        Example: $100 profit on $100,000 account = 0.1% profit_percentage.
        """
        if self.asset is None or self.asset.allocation == 0:
            return 0.0

        return self.profit / self.asset.allocation
