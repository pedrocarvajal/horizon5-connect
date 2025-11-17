from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from services.gateway.models.kline import KlineModel
from services.gateway.models.symbol_info import SymbolInfoModel
from services.gateway.models.trading_fees import TradingFeesModel


class BaseGatewayAdapter(ABC):
    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    @abstractmethod
    def adapt_klines_batch(self, raw_data: List[Any], symbol: str) -> List[KlineModel]:
        pass

    @abstractmethod
    def adapt_symbol_info(self, raw_data: Dict[str, Any]) -> Optional[SymbolInfoModel]:
        pass

    @abstractmethod
    def adapt_trading_fees(
        self, raw_data: Dict[str, Any], futures: bool
    ) -> Optional[TradingFeesModel]:
        pass

    @abstractmethod
    def validate_response(self, raw_data: Any) -> bool:
        pass
