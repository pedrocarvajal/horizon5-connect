import datetime
import json
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from enums.timeframe import Timeframe
from interfaces.indicator import IndicatorInterface
from services.candle import CandleService
from services.ticks import TicksService
from tests.e2e.assets.btcusdt import BTCUSDT


class WrapperIndicator(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _ticks_service: TicksService
    _candle_service: CandleService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, methodName: str = "runTest") -> None:  # noqa: N803
        super().__init__(methodName)

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self, **kwargs: Any) -> None:
        super().setUp()
        test_name = kwargs.get("test_name")

        if test_name is None:
            raise ValueError("Test name is required")

        self._ticks_service = TicksService()
        self._ticks_service.setup(
            asset=BTCUSDT(),
            restore_ticks=False,
            disable_download=True,
        )

    def candles(
        self,
        timeframe: Timeframe,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
        indicators: Optional[List[IndicatorInterface]] = None,
    ) -> List[Dict[str, Any]]:
        service = CandleService(
            timeframe=timeframe,
            indicators=indicators,
        )

        ticks = self._ticks_service.ticks(
            from_date=from_date,
            to_date=to_date,
        )

        for tick in ticks:
            service.on_tick(tick)

        return service.candles

    def get_json_data(self, path: str) -> List[Dict[str, Any]]:
        json_path = Path(__file__).parent.parent / "jsons" / path
        with json_path.open() as f:
            return json.load(f)
