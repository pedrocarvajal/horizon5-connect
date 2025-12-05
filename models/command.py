"""Command model for inter-process communication."""

from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, Field

from enums.command import Command


class CommandModel(BaseModel):
    """Command data structure for queue-based communication.

    Attributes:
        command: Type of command to execute.
        function: Callable to invoke for EXECUTE commands.
        args: Arguments to pass to the function.
    """

    command: Command
    function: Optional[Callable[..., Any]] = Field(default=None)
    args: Optional[Dict[str, Any]] = Field(default=None)
