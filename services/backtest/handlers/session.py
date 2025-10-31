import datetime
from pathlib import Path
from typing import Any

from configs.timezone import TIMEZONE
from services.logging import LoggingService


class SessionHandler:
    _session_id: int
    _session_folder: Path

    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("session_handler")

    def setup(self, **kwargs: Any) -> None:
        self._asset = kwargs.get("asset")

        if self._asset is None:
            raise ValueError("Asset is required")

        self._setup_session()
        self._setup_folders()

    def _setup_session(self) -> None:
        self._session_id = int(datetime.datetime.now(tz=TIMEZONE).timestamp())
        self._log.info(f"Session ID: {self._session_id}")

    def _setup_folders(self) -> None:
        path = f"storage/backtests/{self._asset.symbol}/{self._session_id}"

        self._session_folder = Path(path)
        self._session_folder.mkdir(parents=True, exist_ok=True)
        self._log.info(f"Session folder: {self._session_folder}")

    @property
    def id(self) -> int:
        return self._session_id

    @property
    def folder(self) -> Path:
        return self._session_folder
