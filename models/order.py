import datetime
import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, computed_field

from configs.system import SYSTEM_PREFIX
from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from helpers.get_slug import get_slug
from models.trade import TradeModel
from services.gateway import GatewayService


class OrderModel(BaseModel):
    _id: str
    _demo: bool = False
    _client_order_id: str
    _symbol: str
    _gateway: GatewayService
    _side: Optional[OrderSide]
    _order_type: Optional[OrderType]
    _status: Optional[OrderStatus]
    _volume: float = 0.0
    _executed_volume: float = 0.0
    _price: float = 0.0
    _created_at: datetime.datetime
    _updated_at: datetime.datetime
    trades: List[TradeModel] = []

    def __init__(self) -> None:
        super().__init__()

        self._id = self._get_uuid()
        self._client_order_id = self._get_client_order_id()
        self._status = OrderStatus.ORDER_CREATED
        self._order_type = OrderType.MARKET
        self._created_at = datetime.datetime.now(tz=TIMEZONE).timestamp() * 1000
        self._updated_at = self._created_at

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def to_json(self) -> str:
        return self.model_dump_json()

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

    @computed_field
    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id = value

    @computed_field
    @property
    def demo(self) -> bool:
        return self._demo

    @demo.setter
    def demo(self, value: bool) -> None:
        self._demo = value

    @computed_field
    @property
    def client_order_id(self) -> str:
        return self._client_order_id

    @client_order_id.setter
    def client_order_id(self, value: str) -> None:
        self._client_order_id = value

    @computed_field
    @property
    def symbol(self) -> str:
        return self._symbol

    @symbol.setter
    def symbol(self, value: str) -> None:
        self._symbol = value

    @computed_field
    @property
    def gateway(self) -> GatewayService:
        return self._gateway

    @gateway.setter
    def gateway(self, value: GatewayService) -> None:
        self._gateway = value

    @computed_field
    @property
    def side(self) -> Optional[OrderSide]:
        return self._side

    @side.setter
    def side(self, value: OrderSide) -> None:
        self._side = value

    @computed_field
    @property
    def order_type(self) -> Optional[OrderType]:
        return self._order_type

    @order_type.setter
    def order_type(self, value: OrderType) -> None:
        self._order_type = value

    @computed_field
    @property
    def status(self) -> Optional[OrderStatus]:
        return self._status

    @status.setter
    def status(self, value: OrderStatus) -> None:
        self._status = value

    @computed_field
    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        if value < 0:
            raise ValueError("Volume must be greater than or equal to 0")

        self._volume = value

    @computed_field
    @property
    def executed_volume(self) -> float:
        return self._executed_volume

    @executed_volume.setter
    def executed_volume(self, value: float) -> None:
        if value < 0:
            raise ValueError("Executed volume must be greater than or equal to 0")

        self._executed_volume = value

    @computed_field
    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Price must be greater than or equal to 0")

        self._price = value

    @computed_field
    @property
    def created_at(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self._created_at / 1000, tz=TIMEZONE)

    @created_at.setter
    def created_at(self, value: Union[int, float, datetime.datetime]) -> None:
        if isinstance(value, datetime.datetime):
            self._created_at = int(value.timestamp() * 1000)

        elif isinstance(value, float):
            self._created_at = int(value * 1000)

        else:
            self._created_at = value

    @computed_field
    @property
    def updated_at(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self._updated_at / 1000, tz=TIMEZONE)

    @updated_at.setter
    def updated_at(self, value: Union[int, float, datetime.datetime]) -> None:
        if isinstance(value, datetime.datetime):
            self._updated_at = int(value.timestamp() * 1000)

        elif isinstance(value, float):
            self._updated_at = int(value * 1000)

        else:
            self._updated_at = value
