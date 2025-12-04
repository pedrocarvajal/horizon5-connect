"""Logging service with colored console output and file logging."""

import logging
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any, ClassVar

from colorama import Fore, Style, just_fix_windows_console
from rich.console import Console
from rich.json import JSON

from helpers.get_slug import get_slug

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds color to log level names."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colored level name."""
        level_colors = {
            logging.DEBUG: Fore.CYAN,
            logging.INFO: Fore.WHITE,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.RED + Style.BRIGHT,
            SUCCESS_LEVEL: Fore.GREEN,
        }
        color = level_colors.get(record.levelno, "")
        reset = Style.RESET_ALL

        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class LoggingService:
    """Service for logging messages to console and file with formatting."""

    _name: str = ""
    _prefix: str = ""
    _logs_folder: ClassVar[Path] = Path("logs")
    logger: logging.Logger = logging.getLogger(__name__)

    def debug(self, message: Any) -> None:
        """Log a debug message, formatting dicts/lists as JSON."""
        if isinstance(message, (dict, list)):
            string_io = StringIO()
            console = Console(file=string_io, force_terminal=True, width=120)
            console.print(JSON.from_data(message))
            output = string_io.getvalue().rstrip()
        else:
            output = str(message)

        if self._prefix:
            output = f"{self._prefix} {output}"

        self.logger.debug(output)

    def info(self, message: str) -> None:
        """Log an info message."""
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.info(formatted_message)

    def success(self, message: str) -> None:
        """Log a success message."""
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.log(SUCCESS_LEVEL, formatted_message)

    def title(self, message: str) -> None:
        """Log a title message with separator lines."""
        separator = "=" * 80
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.info(separator)
        self.logger.info(formatted_message)
        self.logger.info(separator)

    def separator(self) -> None:
        """Log a separator line."""
        self.logger.info("=" * 80)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.warning(formatted_message)

    def error(self, message: str) -> None:
        """Log an error message."""
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.error(formatted_message)

    def critical(self, message: str) -> None:
        """Log a critical message."""
        formatted_message = f"{self._prefix} {message}" if self._prefix else message
        self.logger.critical(formatted_message)

    def setup(self, name: str) -> None:
        """Initialize the logger with console and file handlers."""
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
        """Set a prefix to prepend to all log messages."""
        self._prefix = prefix

    def prompt(self, label: str) -> str:
        """Generate a formatted prompt string with timestamp."""
        timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] [INPUT] [{self.logger.name}] > {label}"
