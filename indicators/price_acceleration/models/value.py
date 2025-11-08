import datetime
from typing import Optional

from pydantic import BaseModel


class PriceAccelerationValueModel(BaseModel):
    date: Optional[datetime.datetime] = None
    value: float = 0.0
