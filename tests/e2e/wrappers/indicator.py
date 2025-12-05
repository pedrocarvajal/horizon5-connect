"""Indicator wrapper for end-to-end testing of technical indicators."""

import datetime
import json
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from enums.timeframe import Timeframe
from interfaces.indicator import IndicatorInterface
from models.candle import CandleModel
from services.candle import CandleService
from services.ticks import TicksService
from tests.e2e.assets.btcusdt import BTCUSDT


class WrapperIndicator(unittest.TestCase):
    """
    Base wrapper for end-to-end indicator testing.

    This wrapper provides the core functionality for testing technical indicators
    in an end-to-end context. It handles tick data loading, candle generation,
    and indicator calculation for validation against expected results.

    The wrapper manages:
    - Tick data retrieval through TicksService
    - Candle generation with configurable timeframes
    - Indicator attachment and calculation
    - JSON fixture loading for test validation

    Attributes:
        _ticks_service: Service for loading and managing historical tick data.
        _candle_service: Service for building candles from ticks.
    """

    def __init__(self, method_name: str = "runTest") -> None:
        """
        Initialize the indicator wrapper.

        Args:
            method_name: Name of the test method to run.
        """
        super().__init__(method_name)

        self._ticks_service: TicksService
        self._candle_service: CandleService

    def setUp(self) -> None:
        """
        Set up the test environment with required dependencies.

        Initializes the ticks service with the BTCUSDT asset for testing.
        """
        super().setUp()

        self._ticks_service = TicksService()
        self._ticks_service.setup(asset=BTCUSDT(), restore_ticks=False, disable_download=True)

    def candles(
        self,
        timeframe: Timeframe,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
        indicators: Optional[List[IndicatorInterface]] = None,
    ) -> List[CandleModel]:
        """
        Generate candles with optional indicators for a date range.

        Creates a candle service with the specified timeframe and indicators,
        then processes all ticks within the date range to build candles.

        Args:
            timeframe: The timeframe for candle aggregation.
            from_date: Start date for tick data retrieval.
            to_date: End date for tick data retrieval.
            indicators: Optional list of indicators to attach to candles.

        Returns:
            List of CandleModel instances with indicator values.
        """
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

    def get_json_data(
        self,
        path: str,
    ) -> List[Dict[str, Any]]:
        """
        Load JSON fixture data for test validation.

        Reads a JSON file from the tests/e2e/jsons directory relative
        to this wrapper's location.

        Args:
            path: Relative path to the JSON file within the jsons directory.

        Returns:
            Parsed JSON data as a list of dictionaries.
        """
        json_path = Path(__file__).parent.parent / "fixtures" / path

        with json_path.open() as file:
            return json.load(file)
