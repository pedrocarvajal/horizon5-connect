from enum import Enum


class DBCommand(Enum):
    STORE = "store"
    UPDATE = "update"
    DELETE = "delete"
    KILL = "kill"
