"""Logging service with colored console output and file logging."""

import logging
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any, ClassVar, Dict

from colorama import Back, Fore, Style, just_fix_windows_console
from rich.console import Console
from rich.json import JSON

from vendor.interfaces.logging import LoggingInterface

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds color to log level names."""

    LEVEL_COLORS: ClassVar[Dict[int, str]] = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.WHITE,
        logging.WARNING: Back.LIGHTYELLOW_EX + Fore.BLACK,
        logging.ERROR: Back.LIGHTYELLOW_EX + Fore.RED,
        logging.CRITICAL: Back.LIGHTYELLOW_EX + Fore.RED + Style.BRIGHT,
        SUCCESS_LEVEL: Fore.GREEN,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colored level name."""
        color = self.LEVEL_COLORS.get(record.levelno, "")
        reset = Style.RESET_ALL

        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class LoggingService(LoggingInterface):
    """Service for logging messages to console and file with formatting."""

    LOGS_FOLDER: ClassVar[Path] = Path("logs")
    SEPARATOR_CHARACTER: ClassVar[str] = "="
    SEPARATOR_LENGTH: ClassVar[int] = 80

    _current_date: ClassVar[str] = ""
    _initialized: ClassVar[bool] = False
    _shared_logger: ClassVar[logging.Logger] = logging.getLogger("horizon5")

    def __init__(self) -> None:
        """Initialize the logging service."""
        self._prefix: str = ""

    def critical(self, message: str, **context: Any) -> None:
        """Log a critical message with optional context."""
        formatted_message = self._format_message(message, context)
        self._get_logger().critical(formatted_message)

    def debug(self, message: Any, **context: Any) -> None:
        """Log a debug message with optional context, formatting dicts/lists as JSON."""
        if isinstance(message, (dict, list)):
            string_io = StringIO()
            console = Console(file=string_io, force_terminal=True, width=120)
            console.print(JSON.from_data(message))
            output = string_io.getvalue().rstrip()
        else:
            output = str(message)

        formatted_message = self._format_message(output, context)
        self._get_logger().debug(formatted_message)

    def error(self, message: str, **context: Any) -> None:
        """Log an error message with optional context."""
        formatted_message = self._format_message(message, context)
        self._get_logger().error(formatted_message)

    def info(self, message: str, **context: Any) -> None:
        """Log an info message with optional context."""
        formatted_message = self._format_message(message, context)
        self._get_logger().info(formatted_message)

    def prompt(self, label: str) -> str:
        """Generate a formatted prompt string with timestamp."""
        timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] [INPUT] > {label}"

    def separator(self) -> None:
        """Log a separator line."""
        separator_line = self.SEPARATOR_CHARACTER * self.SEPARATOR_LENGTH
        self._get_logger().info(separator_line)

    def setup_prefix(self, prefix: str) -> None:
        """Set a prefix to prepend to all log messages."""
        self._prefix = prefix

    def success(self, message: str, **context: Any) -> None:
        """Log a success message with optional context."""
        formatted_message = self._format_message(message, context)
        self._get_logger().log(SUCCESS_LEVEL, formatted_message)

    def title(self, message: str) -> None:
        """Log a title message with separator lines."""
        separator_line = self.SEPARATOR_CHARACTER * self.SEPARATOR_LENGTH
        formatted_message = self._format_message(message)
        logger = self._get_logger()
        logger.info(separator_line)
        logger.info(formatted_message)
        logger.info(separator_line)

    def warning(self, message: str, **context: Any) -> None:
        """Log a warning message with optional context."""
        formatted_message = self._format_message(message, context)
        self._get_logger().warning(formatted_message)

    def _ensure_initialized(self) -> None:
        """Ensure logger is initialized with current day's log file."""
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        if not LoggingService._initialized or LoggingService._current_date != today:
            self._initialize_logger(today)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dict as key=value pairs."""
        if not context:
            return ""

        pairs = [f"{key}= {value}" for key, value in context.items()]
        return " | " + ", ".join(pairs)

    def _format_message(self, message: str, context: Dict[str, Any] | None = None) -> str:
        """Format message with prefix and context if set."""
        context_string = self._format_context(context) if context else ""

        if self._prefix:
            return f"{self._prefix} {message}{context_string}"

        return f"{message}{context_string}"

    def _get_logger(self) -> logging.Logger:
        """Get the shared logger, initializing if needed."""
        self._ensure_initialized()
        return LoggingService._shared_logger

    def _initialize_logger(self, date: str) -> None:
        """Initialize or reinitialize the logger for a new day."""
        just_fix_windows_console()

        self.LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

        log_file_name = f"{date}.log"
        log_file_path = self.LOGS_FOLDER / log_file_name

        for handler in LoggingService._shared_logger.handlers[:]:
            handler.close()
            LoggingService._shared_logger.removeHandler(handler)

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

        LoggingService._shared_logger.setLevel(logging.DEBUG)
        LoggingService._shared_logger.addHandler(file_handler)
        LoggingService._shared_logger.addHandler(console_handler)
        LoggingService._shared_logger.propagate = False

        LoggingService._initialized = True
        LoggingService._current_date = date
