# Import your assets here
from typing import Dict

from assets.btcusdt import BTCUSDT
from interfaces.asset import AssetInterface

ASSETS: Dict[str, type[AssetInterface]] = {
    "btcusdt": BTCUSDT,
}
