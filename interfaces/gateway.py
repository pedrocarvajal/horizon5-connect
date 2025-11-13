from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Dict, List, Optional

from services.gateway.models.kline import KlineModel
from services.gateway.models.symbol_info import SymbolInfoModel
from services.gateway.models.trading_fees import TradingFeesModel


class GatewayInterface(ABC):
    @abstractmethod
    def get_klines(
        self,
        futures: bool,
        symbol: str,
        timeframe: str,
        from_date: Optional[int],
        to_date: Optional[int],
        *,
        callback: Callable[[List[KlineModel]], None],
        **kwargs: Any,
    ) -> None:
        pass

    @abstractmethod
    def get_symbol_info(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[SymbolInfoModel]:
        pass

    @abstractmethod
    def get_trading_fees(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[TradingFeesModel]:
        pass

    @abstractmethod
    def get_leverage_info(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[Dict[str, Any]]:
        pass
