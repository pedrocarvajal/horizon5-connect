from typing import Any, Dict

from services.logging import LoggingService


class CommandStoreHandler:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _repositories: Dict[str, Any]
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, repositories: Dict[str, Any], log: LoggingService) -> None:
        self._repositories = repositories
        self._log = log

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def execute(self, command: Dict[str, Any]) -> tuple[bool, bool]:
        if not self._validate_command(command):
            return False, False

        repository_name = command["repository"]
        method_data = command["method"]
        repository = self._get_repository(repository_name)

        if not repository:
            return False, False

        success = self._execute_method(repository, method_data)
        return success, False

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_command(self, command: Dict[str, Any]) -> bool:
        repository_name = command.get("repository")
        method_data = command.get("method")

        if not repository_name:
            self._log.error("Repository is not set")
            return False

        if not method_data:
            self._log.error("Method is not set")
            return False

        method_name = method_data.get("name")
        method_arguments = method_data.get("arguments")

        if not method_name or not method_arguments:
            self._log.error("Method name or arguments are not set")
            return False

        return True

    def _get_repository(self, repository_name: str) -> Any:
        repository = self._repositories.get(repository_name)

        if not repository:
            self._log.error(f"Repository {repository_name} not found")
            return None

        return repository

    def _execute_method(self, repository: Any, method_data: Dict[str, Any]) -> bool:
        method_name = method_data["name"]
        method_arguments = method_data["arguments"]

        try:
            method = getattr(repository, method_name)
            method(**method_arguments)
            return True
        except Exception as e:
            self._log.error(f"Error executing {method_name}: {e}")
            return False
