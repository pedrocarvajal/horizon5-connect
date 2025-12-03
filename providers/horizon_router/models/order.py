from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType


class OrderTradeModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    id: str = Field(default="", description="Trade ID from the gateway/exchange")
    order_id: str = Field(default="", description="Order ID that this trade belongs to")
    symbol: str = Field(default="", description="The trading symbol")
    side: Optional[OrderSide] = Field(default=None, description="Trade side: BUY or SELL")
    price: float = Field(default=0.0, ge=0, description="Trade execution price")
    volume: float = Field(default=0.0, ge=0, description="Trade volume executed")
    commission: float = Field(default=0.0, ge=0, description="Commission paid for this trade")
    commission_asset: str = Field(default="", description="Asset used for commission payment")
    timestamp: Optional[int] = Field(default=None, ge=0, description="Trade execution timestamp in milliseconds")


class OrderLogEntryModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    event: str = Field(description="Type of event")
    status: Optional[str] = Field(default=None, description="Order status at the time of the event")
    message: Optional[str] = Field(default=None, description="Optional message describing the event")
    timestamp: Optional[int] = Field(default=None, ge=0, description="Event timestamp in milliseconds")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional event-specific data")


class OrderListQueryModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    strategy_id: Optional[str] = Field(default=None, description="Filter orders by strategy ID")
    asset_id: Optional[str] = Field(default=None, description="Filter orders by asset ID")
    gateway_id: Optional[str] = Field(default=None, description="Filter orders by gateway ID")
    account_id: Optional[str] = Field(default=None, description="Filter orders by account ID")
    backtest_id: Optional[str] = Field(default=None, description="Filter orders by backtest ID")
    symbol: Optional[str] = Field(default=None, description="Filter orders by symbol")
    side: Optional[str] = Field(default=None, description="Filter orders by side (comma-separated)")
    order_type: Optional[str] = Field(default=None, description="Filter orders by order type (comma-separated)")
    status: Optional[str] = Field(default=None, description="Filter orders by status (comma-separated)")
    backtest: Optional[bool] = Field(default=None, description="Filter orders by backtest flag")
    per_page: Optional[int] = Field(default=15, ge=1, le=100, description="Number of results per page")
    page: Optional[int] = Field(default=1, ge=1, description="Page number")


class OrderCreateModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    strategy_id: str = Field(description="Strategy ID")
    asset_id: str = Field(description="Asset ID")
    gateway_id: Optional[str] = Field(default=None, description="Gateway ID")
    account_id: str = Field(description="Account ID")
    backtest_id: Optional[str] = Field(default=None, description="Backtest ID")
    gateway_order_id: Optional[str] = Field(default=None, description="Gateway order ID")
    backtest: bool = Field(description="Is this a backtest order?")
    symbol: str = Field(min_length=1, description="Order symbol")
    side: OrderSide = Field(description="Order side")
    order_type: OrderType = Field(description="Order type")
    status: Optional[OrderStatus] = Field(default=OrderStatus.OPENING, description="Order status")
    volume: float = Field(gt=0, description="Order volume")
    executed_volume: Optional[float] = Field(default=None, ge=0, description="Executed volume")
    price: float = Field(gt=0, description="Order price")
    close_price: Optional[float] = Field(default=None, ge=0, description="Close price")
    take_profit_price: Optional[float] = Field(default=None, ge=0, description="Take profit price")
    stop_loss_price: Optional[float] = Field(default=None, ge=0, description="Stop loss price")
    commission: Optional[float] = Field(default=None, ge=0, description="Commission amount")
    commission_percentage: Optional[float] = Field(
        default=None, ge=0, le=1, description="Commission percentage (0-1 range)"
    )
    client_order_id: Optional[str] = Field(default=None, description="Client order ID")
    trades: Optional[List[OrderTradeModel]] = Field(default=None, description="Trade history")
    logs: Optional[List[OrderLogEntryModel]] = Field(default=None, description="Order logs")
    variables: Optional[Dict[str, Any]] = Field(default=None, description="Additional variables")

    @field_validator("executed_volume")
    @classmethod
    def validate_executed_volume(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("executed_volume must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_volume_constraints(self) -> "OrderCreateModel":
        if self.executed_volume is not None and self.executed_volume > self.volume:
            raise ValueError("executed_volume cannot exceed volume")
        return self


class OrderUpdateModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    gateway_order_id: Optional[str] = Field(default=None, description="Gateway order ID")
    symbol: Optional[str] = Field(default=None, min_length=1, description="Order symbol")
    side: Optional[OrderSide] = Field(default=None, description="Order side")
    order_type: Optional[OrderType] = Field(default=None, description="Order type")
    status: Optional[OrderStatus] = Field(default=None, description="Order status")
    volume: Optional[float] = Field(default=None, gt=0, description="Order volume")
    executed_volume: Optional[float] = Field(default=None, ge=0, description="Executed volume")
    price: Optional[float] = Field(default=None, gt=0, description="Order price")
    close_price: Optional[float] = Field(default=None, ge=0, description="Close price")
    take_profit_price: Optional[float] = Field(default=None, ge=0, description="Take profit price")
    stop_loss_price: Optional[float] = Field(default=None, ge=0, description="Stop loss price")
    commission: Optional[float] = Field(default=None, ge=0, description="Commission amount")
    commission_percentage: Optional[float] = Field(
        default=None, ge=0, le=1, description="Commission percentage (0-1 range)"
    )
    client_order_id: Optional[str] = Field(default=None, description="Client order ID")
    trades: Optional[List[OrderTradeModel]] = Field(default=None, description="Trade history")
    logs: Optional[List[OrderLogEntryModel]] = Field(default=None, description="Order logs")
    variables: Optional[Dict[str, Any]] = Field(default=None, description="Additional variables")
