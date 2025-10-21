import json
import logging
from pathlib import Path
from typing import ClassVar

from helpers.get_slug import get_slug


class ColoredFormatter(logging.Formatter):
    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET: ClassVar[str] = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"

        return super().format(record)


class LoggingService:
    _name: str
    _logs_folder: ClassVar[Path] = Path("logs")

    def debug(self, message: dict | list | str) -> None:
        if isinstance(message, (dict, list)):
            self.logger.debug(f"\n{json.dumps(message, indent=2, ensure_ascii=False)}")

        else:
            self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def critical(self, message: str) -> None:
        self.logger.critical(message)

    def setup(self, name: str) -> None:
        self._logs_folder.mkdir(parents=True, exist_ok=True)

        log_file_name = get_slug(name) + ".log"
        log_file_path = self._logs_folder / log_file_name

        file_formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] > %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_formatter = ColoredFormatter(
            fmt="[%(asctime)s] [%(levelname)s] > %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(console_formatter)

        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.propagate = False

        self.logger = logging.getLogger(log_file_name)
