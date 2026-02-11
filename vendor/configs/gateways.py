"""Gateway configuration and initialization for exchange integrations."""

from typing import Any, Dict

from vendor.services.gateway.gateways.binance import Binance

GATEWAYS: Dict[str, Dict[str, Any]] = {
    "binance": {
        "class": Binance,
        "kwargs": {},
    },
}
