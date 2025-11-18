from typing import Dict

from helpers.get_env import get_env
from interfaces.gateway import GatewayInterface
from services.gateway.gateways.binance import Binance

sandbox = get_env("BINANCE_TESTNET", default=True)
api_key = get_env("BINANCE_API_KEY")
api_secret = get_env("BINANCE_API_SECRET")

if sandbox:
    api_key = get_env("BINANCE_TESTNET_API_KEY")
    api_secret = get_env("BINANCE_TESTNET_API_SECRET")

GATEWAYS: Dict[str, type[GatewayInterface]] = {
    "binance": {
        "class": Binance,
        "kwargs": {
            "sandbox": sandbox,
            "api_key": api_key,
            "api_secret": api_secret,
        },
    }
}
