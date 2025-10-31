import re
import unicodedata
from typing import Dict, Optional


def ascii(text: str) -> str:
    # Remove accentuated characters, basic version
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def get_slug(
    title: str,
    separator: str = "-",
    dictionary: Optional[Dict[str, str]] = None,
) -> str:
    if dictionary is None:
        dictionary = {"@": "at"}

    # 1. Always do ascii conversion (since language is always English)
    title = ascii(title)

    # 2. Flip underscores/dashes
    flip = "_" if separator == "-" else "-"
    title = re.sub(rf"[{re.escape(flip)}]+", separator, title)

    # 3. Replace dictionary words, wrapped with separator
    dict_with_separators = {
        k: f"{separator}{v}{separator}" for k, v in dictionary.items()
    }
    for key, val in dict_with_separators.items():
        title = title.replace(key, val)

    title = title.lower()
    allowed = rf"[^{re.escape(separator)}\w\s]+"
    title = re.sub(allowed, "", title, flags=re.UNICODE)

    # 5. Replace all separator characters and whitespace by a single separator
    title = re.sub(rf"[{re.escape(separator)}\s]+", separator, title, flags=re.UNICODE)

    # 6. Trim separator from ends
    return title.strip(separator)
