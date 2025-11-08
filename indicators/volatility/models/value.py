import datetime
from typing import Optional


class VolatilityValueModel:
    date: Optional[datetime.datetime] = None
    value: float
