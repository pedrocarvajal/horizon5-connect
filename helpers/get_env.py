# Code reviewed on 2025-11-19 by pedrocarvajal

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable value.

    Args:
        key: Environment variable key
        default: Default value if key doesn't exist (default: None)

    Returns:
        Environment variable value or default if key doesn't exist
    """
    return os.getenv(key, default)
