import datetime
from pathlib import Path

from configs.timezone import TIMEZONE
from interfaces.asset import AssetInterface
from services.logging import LoggingService


class SessionHandler:
    _session_id: int
    _session_folder: Path

    def __init__(self, asset: AssetInterface) -> None:
        self._asset = asset
        self._log = LoggingService()
        self._log.setup("session_handler")

    def setup(self) -> None:
        self._session_id = int(datetime.datetime.now(tz=TIMEZONE).timestamp())
        self._session_folder = Path(
            f"storage/backtests/{self._asset.symbol}/{self._session_id}"
        )

        self._session_folder.mkdir(parents=True, exist_ok=True)

        self._log.info(f"Session ID: {self._session_id}")
        self._log.info(f"Session folder: {self._session_folder}")

    @property
    def id(self) -> int:
        return self._session_id

    @property
    def folder(self) -> Path:
        return self._session_folder
