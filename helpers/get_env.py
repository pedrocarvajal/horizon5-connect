# Code reviewed on 2025-11-19 by pedrocarvajal

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable value.

    Args:
        key: Environment variable key
        default: Default value if key doesn't exist (default: None)
        required: If True, raises ValueError when variable is not set (default: False)

    Returns:
        Environment variable value or default if key doesn't exist

    Raises:
        ValueError: If required=True and the environment variable is not set
    """
    value = os.getenv(key, default)

    if required and value is None:
        raise ValueError(f"Environment variable '{key}' is required but not set.")

    return value
