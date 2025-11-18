# Last coding review: 2025-11-17 17:04:05

from typing import Any, Dict, List, Optional

from configs.gateways import GATEWAYS
from interfaces.gateway import GatewayInterface
from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_position import GatewayPositionModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trade import GatewayTradeModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from services.logging import LoggingService


class GatewayService(GatewayInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _name: str
    _sandbox: bool
    _gateways: Dict[str, Any]

    _gateway: GatewayInterface
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        gateway: str,
        **kwargs: Any,
    ) -> None:
        self._log = LoggingService()
        self._log.setup(name="gateway_service")

        self._gateways = GATEWAYS
        self._name = gateway
        self._sandbox = kwargs.get("sandbox", False)

        self._setup()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        self._gateway.get_klines(**kwargs)

    def get_symbol_info(
        self,
        **kwargs: Any,
    ) -> Optional[GatewaySymbolInfoModel]:
        return self._gateway.get_symbol_info(**kwargs)

    def get_trading_fees(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayTradingFeesModel]:
        return self._gateway.get_trading_fees(**kwargs)

    def get_leverage_info(
        self,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        return self._gateway.get_leverage_info(**kwargs)

    def get_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        return self._gateway.get_order(**kwargs)

    async def stream(
        self,
        **kwargs: Any,
    ) -> None:
        await self._gateway.stream(**kwargs)

    def place_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        return self._gateway.place_order(**kwargs)

    def cancel_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        return self._gateway.cancel_order(**kwargs)

    def modify_order(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        return self._gateway.modify_order(**kwargs)

    def set_leverage(
        self,
        **kwargs: Any,
    ) -> bool:
        return self._gateway.set_leverage(**kwargs)

    def get_account(
        self,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        return self._gateway.get_account(
            **kwargs,
        )

    def get_orders(
        self,
        **kwargs: Any,
    ) -> List[GatewayOrderModel]:
        return self._gateway.get_orders(**kwargs)

    def get_trades(
        self,
        **kwargs: Any,
    ) -> List[GatewayTradeModel]:
        return self._gateway.get_trades(**kwargs)

    def get_positions(
        self,
        **kwargs: Any,
    ) -> List[GatewayPositionModel]:
        return self._gateway.get_positions(**kwargs)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _setup(self) -> None:
        if self._name not in self._gateways:
            raise ValueError(f"Gateway {self._name} not found")

        self._log.info(f"Setting up gateway {self._name}")

        if self._sandbox:
            self._gateways[self._name]["kwargs"]["sandbox"] = True

        self._gateway = self._gateways[self._name]["class"](
            **self._gateways[self._name]["kwargs"],
        )

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self._name
