# Code reviewed on 2025-11-19 by pedrocarvajal

import re
import unicodedata
from typing import Dict, Optional


def ascii(text: str) -> str:
    """
    Remove accentuated characters, converting to ASCII.

    Args:
        text: Text with potentially accented characters

    Returns:
        ASCII version of text with accents removed
    """
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def get_slug(
    title: str,
    separator: str = "-",
    dictionary: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate URL-friendly slug from a title.

    Args:
        title: Title to convert to slug
        separator: Separator character (default: "-")
        dictionary: Custom replacement dictionary (default: {"@": "at"})

    Returns:
        URL-friendly slug string
    """
    if dictionary is None:
        dictionary = {"@": "at"}

    title = ascii(title)

    flip = "_" if separator == "-" else "-"
    title = re.sub(rf"[{re.escape(flip)}]+", separator, title)

    dict_with_separators = {
        k: f"{separator}{v}{separator}" for k, v in dictionary.items()
    }
    for key, val in dict_with_separators.items():
        title = title.replace(key, val)

    title = title.lower()
    allowed = rf"[^{re.escape(separator)}\w\s]+"
    title = re.sub(allowed, "", title, flags=re.UNICODE)

    title = re.sub(rf"[{re.escape(separator)}\s]+", separator, title, flags=re.UNICODE)

    return title.strip(separator)
