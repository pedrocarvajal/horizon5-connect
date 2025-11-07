import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any, List, Optional

from services.logging import LoggingService


class ScriptExecutor:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _log: LoggingService
    _file_path: Path
    _class_name: str
    _method_name: str
    _method_args: Optional[List[str]]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        file_path: Path,
        class_name: str,
        method_name: str,
        method_args: Optional[List[str]] = None,
    ) -> None:
        self._log = LoggingService()
        self._log.setup("script")

        self._file_path = file_path
        self._class_name = class_name
        self._method_name = method_name
        self._method_args = method_args

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def execute(self) -> Any:
        module = self._load_module_from_path()
        target_class = self._get_class_from_module(module)
        instance = target_class()

        result = self._execute_method_on_instance(instance)

        if result is not None:
            self._log.info(str(result))

        return result

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _exit_with_error(self, message: str) -> None:
        self._log.error(message)
        sys.exit(1)

    def _load_module_from_path(self) -> Any:
        if not self._file_path.exists():
            self._exit_with_error(f"File {self._file_path} does not exist")

        module_spec = importlib.util.spec_from_file_location(
            "dynamic_module", self._file_path
        )

        if module_spec is None or module_spec.loader is None:
            self._exit_with_error(f"Could not load module from {self._file_path}")

        module = importlib.util.module_from_spec(module_spec)
        sys.modules["dynamic_module"] = module
        module_spec.loader.exec_module(module)

        return module

    def _get_class_from_module(self, module: Any) -> Any:
        if not hasattr(module, self._class_name):
            self._exit_with_error(
                f"Class '{self._class_name}' not found in {self._file_path}"
            )

        return getattr(module, self._class_name)

    def _execute_method_on_instance(self, instance: Any) -> Any:
        if not hasattr(instance, self._method_name):
            self._exit_with_error(
                f"Method '{self._method_name}' not found in class '{self._class_name}'"
            )

        method = getattr(instance, self._method_name)
        return method(*self._method_args) if self._method_args else method()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute any class method dynamically",
    )

    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the Python file",
    )

    parser.add_argument(
        "--class",
        dest="class_name",
        type=str,
        required=True,
        help="Class name to instantiate",
    )

    parser.add_argument(
        "--method",
        type=str,
        required=True,
        help="Method name to execute",
    )

    parser.add_argument(
        "--args",
        type=str,
        nargs="*",
        help="Arguments to pass to the method",
    )

    args = parser.parse_args()
    file_path = Path(args.file).resolve()

    executor = ScriptExecutor(
        file_path=file_path,
        class_name=args.class_name,
        method_name=args.method,
        method_args=args.args,
    )

    executor.execute()


if __name__ == "__main__":
    main()
