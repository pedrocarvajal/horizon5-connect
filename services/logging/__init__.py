import logging
from pathlib import Path
from typing import Any, ClassVar

from colorama import Fore, Style, just_fix_windows_console

from helpers.get_slug import get_slug


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        level_colors = {
            logging.DEBUG: Fore.CYAN,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.RED + Style.BRIGHT,
        }
        color = level_colors.get(record.levelno, "")
        reset = Style.RESET_ALL

        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class LoggingService:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _name: str
    _prefix: str = ""
    _logs_folder: ClassVar[Path] = Path("logs")

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def debug(self, message: Any) -> None:
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.debug(formatted_message)

    def info(self, message: str) -> None:
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.info(formatted_message)

    def warning(self, message: str) -> None:
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.warning(formatted_message)

    def error(self, message: str) -> None:
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.error(formatted_message)

    def critical(self, message: str) -> None:
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.critical(formatted_message)

    def setup(self, name: str) -> None:
        just_fix_windows_console()

        self._logs_folder.mkdir(parents=True, exist_ok=True)

        log_file_name = get_slug(name) + ".log"
        log_file_path = self._logs_folder / log_file_name

        self.logger = logging.getLogger(log_file_name)

        if self.logger.hasHandlers():
            return

        file_formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] > %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_formatter = ColoredFormatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] > %(message)s",
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

    def setup_prefix(self, prefix: str) -> None:
        self._prefix = prefix
