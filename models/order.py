import datetime
import uuid
from typing import Any, List, Optional

from pydantic import BaseModel

from configs.system import SYSTEM_PREFIX
from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from helpers.get_slug import get_slug
from models.tick import TickModel
from models.trade import TradeModel
from services.gateway import GatewayService
from services.logging import LoggingService


class OrderModel(BaseModel):
    _id: str
    _demo: bool = False
    _client_order_id: str
    _symbol: str = ""
    _gateway: Optional[GatewayService] = None
    _side: Optional[OrderSide] = None
    _order_type: Optional[OrderType] = None
    _status: Optional[OrderStatus] = None
    _volume: float = 0.0
    _executed_volume: float = 0.0
    _price: float = 0.0
    _close_price: float = 0.0
    _take_profit_price: float = 0.0
    _stop_loss_price: float = 0.0
    _debug: dict[str, Any] = {}
    _created_at: datetime.datetime
    _updated_at: datetime.datetime
    trades: List[TradeModel] = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        gateway = kwargs.get("gateway")
        demo = kwargs.get("demo")
        symbol = kwargs.get("symbol")
        side = kwargs.get("side")
        price = kwargs.get("price")
        take_profit_price = kwargs.get("take_profit_price")
        stop_loss_price = kwargs.get("stop_loss_price")
        volume = kwargs.get("volume")
        debug = kwargs.get("debug", {})
        created_at = kwargs.get("created_at", datetime.datetime.now(tz=TIMEZONE))
        updated_at = kwargs.get("updated_at", datetime.datetime.now(tz=TIMEZONE))

        self._log = LoggingService()
        self._log.setup("order_model")

        self._id = self._get_uuid()
        self._client_order_id = self._get_client_order_id()
        self._status = OrderStatus.OPENING
        self._order_type = OrderType.MARKET

        self.gateway = gateway
        self.demo = demo
        self.symbol = symbol
        self.side = side
        self.price = price
        self.take_profit_price = take_profit_price
        self.stop_loss_price = stop_loss_price
        self.volume = volume
        self.debug = debug
        self.created_at = created_at
        self.updated_at = updated_at

        self._log.setup_prefix(f"[{self.id}]")

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
        self._log.info("Executing order")

        if self._demo:
            self.status = OrderStatus.OPENED
            self.executed_volume = self.volume

    def close(self) -> None:
        self._log.info("Closing order")

        if self._demo:
            self.status = OrderStatus.CLOSED

    def _get_uuid(self) -> str:
        return str(uuid.uuid4())

    def _get_client_order_id(self) -> str:
        max_length = 16
        max_length_for_system_prefix = 4

        id = self._id.split("-")[-1]
        client_order_id = get_slug(f"{SYSTEM_PREFIX}-{id}")[:16].lower()

        if len(SYSTEM_PREFIX) > max_length_for_system_prefix:
            raise ValueError("System prefix must be less than 4 characters.")

        if len(client_order_id) > max_length:
            raise ValueError("Client order ID must be less than 16 characters.")

        return client_order_id

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id = value

    @property
    def demo(self) -> bool:
        return self._demo

    @demo.setter
    def demo(self, value: bool) -> None:
        self._demo = value

    @property
    def client_order_id(self) -> str:
        return self._client_order_id

    @client_order_id.setter
    def client_order_id(self, value: str) -> None:
        self._client_order_id = value

    @property
    def symbol(self) -> str:
        return self._symbol

    @symbol.setter
    def symbol(self, value: str) -> None:
        self._symbol = value

    @property
    def gateway(self) -> Optional[GatewayService]:
        return self._gateway

    @gateway.setter
    def gateway(self, value: GatewayService) -> None:
        self._gateway = value

    @property
    def side(self) -> Optional[OrderSide]:
        return self._side

    @side.setter
    def side(self, value: OrderSide) -> None:
        self._side = value

    @property
    def order_type(self) -> Optional[OrderType]:
        return self._order_type

    @order_type.setter
    def order_type(self, value: OrderType) -> None:
        self._order_type = value

    @property
    def status(self) -> Optional[OrderStatus]:
        return self._status

    @status.setter
    def status(self, value: OrderStatus) -> None:
        self._status = value

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        if value < 0:
            raise ValueError("Volume must be greater than or equal to 0")
        self._volume = value

    @property
    def executed_volume(self) -> float:
        return self._executed_volume

    @executed_volume.setter
    def executed_volume(self, value: float) -> None:
        if value < 0:
            raise ValueError("Executed volume must be greater than or equal to 0")
        self._executed_volume = value

    @property
    def filled(self) -> bool:
        return self._volume > 0 and self._executed_volume >= self._volume

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Price must be greater than or equal to 0")
        self._price = value

    @property
    def close_price(self) -> float:
        return self._close_price

    @close_price.setter
    def close_price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Close price must be greater than or equal to 0")
        self._close_price = value

    @property
    def take_profit_price(self) -> float:
        return self._take_profit_price

    @take_profit_price.setter
    def take_profit_price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Take profit price must be greater than or equal to 0")
        self._take_profit_price = value

    @property
    def stop_loss_price(self) -> float:
        return self._stop_loss_price

    @stop_loss_price.setter
    def stop_loss_price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Stop loss price must be greater than or equal to 0")
        self._stop_loss_price = value

    @property
    def profit(self) -> float:
        if self._side is OrderSide.SELL:
            return (self._price - self._close_price) * self._volume

        return (self._close_price - self._price) * self._volume

    @property
    def profit_percentage(self) -> float:
        if self._price == 0:
            return 0.0

        if self._side is OrderSide.SELL:
            return (self._price - self._close_price) / self._price

        return (self._close_price - self._price) / self._price

    @property
    def debug(self) -> dict[str, Any]:
        return self._debug

    @debug.setter
    def debug(self, value: dict[str, Any]) -> None:
        self._debug = value

    @property
    def created_at(self) -> datetime.datetime:
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime.datetime) -> None:
        self._created_at = value

    @property
    def updated_at(self) -> datetime.datetime:
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime.datetime) -> None:
        self._updated_at = value
