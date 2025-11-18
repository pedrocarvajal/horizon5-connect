from typing import Any, Dict, List, Optional

from interfaces.gateway import GatewayInterface
from services.gateway.gateways.binance.components.account import AccountComponent
from services.gateway.gateways.binance.components.kline import KlineComponent
from services.gateway.gateways.binance.components.order import OrderComponent
from services.gateway.gateways.binance.components.position import PositionComponent
from services.gateway.gateways.binance.components.stream import StreamComponent
from services.gateway.gateways.binance.components.symbol import SymbolComponent
from services.gateway.gateways.binance.components.trade import TradeComponent
from services.gateway.gateways.binance.models.config import BinanceConfigModel
from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_leverage_info import GatewayLeverageInfoModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_position import GatewayPositionModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trade import GatewayTradeModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from services.logging import LoggingService


class Binance(GatewayInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _config: BinanceConfigModel
    _account_component: AccountComponent
    _kline_component: KlineComponent
    _order_component: OrderComponent
    _position_component: PositionComponent
    _stream_component: StreamComponent
    _symbol_component: SymbolComponent
    _trade_component: TradeComponent

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        self._log = LoggingService()
        self._log.setup("gateway_binance")

        sandbox = kwargs.get("sandbox", False)
        api_key = kwargs.get("api_key", "")
        api_secret = kwargs.get("api_secret", "")

        if sandbox:
            fapi_url = "https://testnet.binancefuture.com/fapi/v1"
            fapi_v2_url = "https://testnet.binancefuture.com/fapi/v2"
            fapi_ws_url = "wss://stream.binancefuture.com/ws"
        else:
            fapi_url = "https://fapi.binance.com/fapi/v1"
            fapi_v2_url = "https://fapi.binance.com/fapi/v2"
            fapi_ws_url = "wss://fstream.binance.com/ws"

        self._config = BinanceConfigModel(
            api_key=api_key,
            api_secret=api_secret,
            fapi_url=fapi_url,
            fapi_v2_url=fapi_v2_url,
            fapi_ws_url=fapi_ws_url,
            sandbox=sandbox,
        )

        self._account_component = AccountComponent(
            config=self._config,
        )

        self._order_component = OrderComponent(
            config=self._config,
        )

        self._position_component = PositionComponent(
            config=self._config,
        )

        self._trade_component = TradeComponent(
            config=self._config,
        )

        self._stream_component = StreamComponent(
            config=self._config,
        )

        self._kline_component = KlineComponent(
            config=self._config,
        )

        self._symbol_component = SymbolComponent(
            config=self._config,
        )

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        self._kline_component.get_klines(**kwargs)

    def get_symbol_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewaySymbolInfoModel]:
        return self._symbol_component.get_symbol_info(**kwargs)

    def get_trading_fees(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayTradingFeesModel]:
        return self._symbol_component.get_trading_fees(**kwargs)

    def get_leverage_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayLeverageInfoModel]:
        return self._symbol_component.get_leverage_info(**kwargs)

    async def stream(
        self,
        **kwargs: Any,
    ) -> None:
        await self._stream_component.stream(**kwargs)

    def place_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        return self._order_component.place_order(**kwargs)

    def cancel_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        return self._order_component.cancel_order(**kwargs)

    def modify_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        return self._order_component.modify_order(**kwargs)

    def set_leverage(
        self,
        **kwargs: Any,
    ) -> bool:
        return self._symbol_component.set_leverage(**kwargs)

    def get_account(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        return self._account_component.get_account(**kwargs)

    def get_orders(
        self,
        **kwargs: Any,
    ) -> List[GatewayOrderModel]:
        return self._order_component.get_orders(**kwargs)

    def get_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        return self._order_component.get_order(**kwargs)

    def get_trades(
        self,
        **kwargs: Any,
    ) -> List[GatewayTradeModel]:
        return self._trade_component.get_trades(**kwargs)

    def get_positions(
        self,
        **kwargs: Any,
    ) -> List[GatewayPositionModel]:
        return self._position_component.get_positions(**kwargs)

    def get_verification(
        self,
        **kwargs: Any,
    ) -> Dict[str, bool]:
        return self._account_component.get_verification(**kwargs)
