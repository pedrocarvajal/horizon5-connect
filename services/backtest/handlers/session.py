import datetime
from multiprocessing import Queue
from typing import Any

from configs.timezone import TIMEZONE
from services.logging import LoggingService


class SessionHandler:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _session_id: int
    _db_commands_queue: Queue

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("session_handler")

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setup(self, **kwargs: Any) -> None:
        self._asset = kwargs.get("asset")
        self._db_commands_queue = kwargs.get("db_commands_queue")

        if self._db_commands_queue is None:
            raise ValueError("DB commands queue is required")

        if self._asset is None:
            raise ValueError("Asset is required")

        self._setup_session()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _setup_session(self) -> None:
        self._session_id = int(datetime.datetime.now(tz=TIMEZONE).timestamp())
        self._log.info(f"Session ID: {self._session_id}")

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def id(self) -> int:
        return self._session_id
