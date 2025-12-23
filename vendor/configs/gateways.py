"""Gateway configuration and initialization for exchange integrations."""

from typing import Any, Dict

from vendor.helpers.get_env import get_env
from vendor.services.gateway.gateways.metaapi import MetaApi

metaapi_auth_token = get_env("METAAPI_AUTH_TOKEN")
metaapi_account_id = get_env("METAAPI_ACCOUNT_ID")

GATEWAYS: Dict[str, Dict[str, Any]] = {
    "metaapi": {
        "class": MetaApi,
        "kwargs": {
            "auth_token": metaapi_auth_token,
            "account_id": metaapi_account_id,
        },
    },
}
