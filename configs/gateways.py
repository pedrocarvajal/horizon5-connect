from typing import Any, Dict

from helpers.get_env import get_env
from services.gateway.gateways.binance import Binance

sandbox_env = get_env("BINANCE_TESTNET", default="True")
sandbox = sandbox_env.lower() in ("true", "1", "yes", "on", 1) if sandbox_env else True
api_key = get_env("BINANCE_API_KEY")
api_secret = get_env("BINANCE_API_SECRET")

if sandbox:
    api_key = get_env("BINANCE_TESTNET_API_KEY")
    api_secret = get_env("BINANCE_TESTNET_API_SECRET")

GATEWAYS: Dict[str, Dict[str, Any]] = {
    "binance": {
        "class": Binance,
        "kwargs": {
            "sandbox": sandbox,
            "api_key": api_key,
            "api_secret": api_secret,
        },
    }
}
