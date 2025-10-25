from configs.gateways import GATEWAYS
from interfaces.gateway import GatewayInterface


class GatewayService(GatewayInterface):
    _gateway_name: str
    _gateway_credentials: dict[str, str]
    _gateway: GatewayInterface

    def __init__(self, gateway: str, credentials: dict[str, str]) -> None:
        self._gateways = GATEWAYS
        self._gateway_name = gateway
        self._gateway_credentials = credentials

        self._setup()

    def _setup(self) -> None:
        if self._gateway_name not in self._gateways:
            raise ValueError(f"Gateway {self._gateway_name} not found")

        self._gateway = self._gateways[self._gateway_name](self._gateway_credentials)
