from typing import Dict

from interfaces.gateway import GatewayInterface
from services.gateway.gateways.binance import Binance

GATEWAYS: Dict[str, type[GatewayInterface]] = {
    "binance": {
        "class": Binance,
    }
}
