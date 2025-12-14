"""Gateway configuration and initialization for exchange integrations."""

from typing import Any, Dict

from vendor.helpers.get_env import get_env
from vendor.services.gateway.gateways.binance import Binance
from vendor.services.gateway.gateways.metaapi import MetaApi

sandbox_env = get_env("BINANCE_TESTNET", default="True")
sandbox = sandbox_env.lower() in ("true", "1", "yes", "on", 1) if sandbox_env else True
api_key = get_env("BINANCE_API_KEY")
api_secret = get_env("BINANCE_API_SECRET")

if sandbox:
    api_key = get_env("BINANCE_TESTNET_API_KEY")
    api_secret = get_env("BINANCE_TESTNET_API_SECRET")

metaapi_auth_token = get_env("METAAPI_AUTH_TOKEN")
metaapi_account_id = get_env("METAAPI_ACCOUNT_ID")

GATEWAYS: Dict[str, Dict[str, Any]] = {
    "binance": {
        "class": Binance,
        "kwargs": {
            "sandbox": sandbox,
            "api_key": api_key,
            "api_secret": api_secret,
        },
    },
    "metaapi": {
        "class": MetaApi,
        "kwargs": {
            "auth_token": metaapi_auth_token,
            "account_id": metaapi_account_id,
        },
    },
}
