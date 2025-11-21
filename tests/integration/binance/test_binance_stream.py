# Code reviewed on 2025-11-21 by Claude (refactor-tests.md workflow)

import asyncio
import contextlib
from typing import List

from models.tick import TickModel
from tests.integration.binance.wrappers.binance import BinanceWrapper


class TestBinanceStream(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _STREAM_NAME: str = "btcusdt@bookTicker"
    _STREAM_TIMEOUT_SECONDS: int = 5

    # ───────────────────────────────────────────────────────────
    # SETUP
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_stream")

    # ───────────────────────────────────────────────────────────
    # TESTS
    # ───────────────────────────────────────────────────────────
    def test_stream(self) -> None:
        """Test WebSocket stream connection and tick data reception.

        Verifies:
        - Stream establishes connection successfully
        - Tick data is received within timeout period
        - Tick model contains valid price, bid/ask, and timestamp data
        - Data is marked as non-simulated
        """
        all_ticks: List[TickModel] = []

        async def callback(tick: TickModel) -> None:
            all_ticks.append(tick)

        async def run_stream() -> None:
            await self._gateway.stream(
                streams=[self._STREAM_NAME],
                callback=callback,
            )

        async def test_with_timeout() -> None:
            stream_task = asyncio.create_task(run_stream())
            await asyncio.sleep(self._STREAM_TIMEOUT_SECONDS)
            stream_task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await stream_task

        asyncio.run(test_with_timeout())

        # ───────────────────────────────────────────────────────────
        # ASSERTIONS
        # ───────────────────────────────────────────────────────────
        assert len(all_ticks) > 0, f"Should receive at least 1 tick, got {len(all_ticks)}"
        assert all(isinstance(t, TickModel) for t in all_ticks), "All ticks should be TickModel"
        assert all_ticks[0].price > 0, f"Price should be > 0, got {all_ticks[0].price}"
        assert all_ticks[0].bid_price > 0, f"Bid price should be > 0, got {all_ticks[0].bid_price}"
        assert all_ticks[0].ask_price > 0, f"Ask price should be > 0, got {all_ticks[0].ask_price}"
        assert all_ticks[0].date is not None, "Date should not be None"
        assert all_ticks[0].is_simulated is False, f"is_simulated should be False, got {all_ticks[0].is_simulated}"
