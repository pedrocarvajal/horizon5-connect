from typing import Dict

from helpers.get_env import get_env
from interfaces.gateway import GatewayInterface
from services.gateway.gateways.binance import Binance

GATEWAYS: Dict[str, type[GatewayInterface]] = {
    "binance": {
        "class": Binance,
        "kwargs": {
            "api_key": get_env("BINANCE_API_KEY"),
            "api_secret": get_env("BINANCE_API_SECRET"),
        },
    }
}
