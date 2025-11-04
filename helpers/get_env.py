import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, default: Optional[str] = None) -> str:
    return os.getenv(key, default)
