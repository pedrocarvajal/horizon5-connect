from models.tick import TickModel
from models.trade import TradeModel
from services.gateway import GatewayService


class AssetInterface:
    _symbol: str
    _gateway: GatewayService

    def setup(self) -> None:
        pass

    def on_tick(self, tick: TickModel) -> None:
        pass

    def on_transaction(self, trade: TradeModel) -> None:
        pass

    def on_end(self) -> None:
        pass

    @property
    def symbol(self) -> str:
        return self._symbol.lower()

    @property
    def gateway(self) -> GatewayService:
        return self._gateway
