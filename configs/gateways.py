from interfaces.gateway import GatewayInterface
from services.gateway.gateways.binance import Binance

GATEWAYS: dict[str, type[GatewayInterface]] = {
    "binance": {
        "class": Binance,
        "variables": {
            "api_key": None,
            "api_secret": None,
        },
    }
}
