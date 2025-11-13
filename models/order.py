import datetime
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from configs.system import SYSTEM_PREFIX
from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from helpers.get_slug import get_slug
from models.tick import TickModel
from models.trade import TradeModel
from services.gateway import GatewayService
from services.logging import LoggingService


class OrderModel(BaseModel):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    backtest: bool = False
    backtest_id: Optional[str] = None
    strategy_id: Optional[str] = None
    symbol: str = ""
    gateway: Optional[GatewayService] = None
    side: Optional[OrderSide] = None
    order_type: Optional[OrderType] = Field(default=OrderType.MARKET)
    status: Optional[OrderStatus] = Field(default=OrderStatus.OPENING)
    volume: float = Field(default=0.0, ge=0)
    executed_volume: float = Field(default=0.0, ge=0)
    price: float = Field(default=0.0, ge=0)
    close_price: float = Field(default=0.0, ge=0)
    take_profit_price: float = Field(default=0.0, ge=0)
    stop_loss_price: float = Field(default=0.0, ge=0)

    commission: float = Field(default=0.0, ge=0)
    commission_percentage: float = Field(default=0.0, ge=0)

    trades: List[TradeModel] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)

    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self._log = LoggingService()
        self._log.setup("order_model")
        self._log.setup_prefix(f"[{self.id}]")

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "status" and hasattr(self, "status"):
            self._track_status_change(value)

        super().__setattr__(name, value)

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def check_if_ready_to_close_take_profit(self, tick: TickModel) -> bool:
        return (
            self.status is OrderStatus.OPENED
            and self.take_profit_price > 0
            and tick.price >= self.take_profit_price
        )

    def check_if_ready_to_close_stop_loss(self, tick: TickModel) -> bool:
        return (
            self.status is OrderStatus.OPENED
            and self.stop_loss_price > 0
            and tick.price <= self.stop_loss_price
        )

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "backtest": self.backtest,
            "backtest_id": self.backtest_id,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "gateway": self.gateway.name,
            "side": self.side.value,
            "order_type": self.order_type.value,
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

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _track_status_change(self, status: OrderStatus) -> None:
        self.logs.append(
            {
                "event": "status_change",
                "status": status.value,
            }
        )

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @computed_field
    @property
    def client_order_id(self) -> str:
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
        return self.volume > 0 and self.executed_volume >= self.volume

    @computed_field
    @property
    def profit(self) -> float:
        if self.side is OrderSide.SELL:
            return (self.price - self.close_price) * self.volume

        return (self.close_price - self.price) * self.volume

    @computed_field
    @property
    def profit_percentage(self) -> float:
        if self.price == 0:
            return 0.0

        if self.side is OrderSide.SELL:
            return (self.price - self.close_price) / self.price

        return (self.close_price - self.price) / self.price
