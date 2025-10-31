from enum import Enum


class OrderEvent(Enum):
    OPEN = "open"
    OPENED = "opened"
    CANCEL = "cancel"
    CANCELLED = "cancelled"
    MODIFY = "modify"
    MODIFIED = "modified"
