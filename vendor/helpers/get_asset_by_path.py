"""Asset dynamic loading utilities."""

import importlib
import inspect

from vendor.interfaces.asset import AssetInterface
from vendor.services.logging import LoggingService


def get_asset_by_path(
    path: str,
) -> type[AssetInterface]:
    """
    Load asset class from module path.

    Args:
        path: Python module path (e.g., "assets.xauusd", "assets.btcusdt")

    Returns:
        AssetInterface class (not instantiated)

    Raises:
        ModuleNotFoundError: If module doesn't exist
        ValueError: If no asset class found in module
    """
    log = LoggingService()

    try:
        module = importlib.import_module(path)
    except ModuleNotFoundError as exc:
        error_msg = f"Asset module not found: {path}"
        log.error(error_msg)
        raise ModuleNotFoundError(error_msg) from exc

    asset_classes = [
        member
        for _, member in inspect.getmembers(module, inspect.isclass)
        if issubclass(member, AssetInterface) and member is not AssetInterface
    ]

    if not asset_classes:
        error_msg = f"Asset module must define an AssetInterface implementation: {path}"
        log.error(error_msg)
        raise ValueError(error_msg)

    return asset_classes[0]
