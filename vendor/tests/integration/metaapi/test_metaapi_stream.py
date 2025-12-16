"""Integration tests for MetaAPI streaming operations."""

import asyncio
import contextlib
from typing import List

from vendor.models.tick import TickModel
from vendor.tests.integration.metaapi.wrappers.metaapi import MetaApiWrapper


class TestMetaApiStream(MetaApiWrapper):
    """Integration tests for MetaAPI real-time price streaming via REST polling."""

    _STREAM_TIMEOUT_SECONDS: int = 10

    def test_stream_receives_valid_ticks(self) -> None:
        """Test streaming real-time price data via REST polling."""
        all_ticks: List[TickModel] = []

        async def collect_tick(tick: TickModel) -> None:
            all_ticks.append(tick)

        async def run_stream_with_timeout() -> None:
            stream_task = asyncio.create_task(
                self._gateway.stream(
                    symbols=[self._SYMBOL],
                    callback=collect_tick,
                )
            )
            await asyncio.sleep(self._STREAM_TIMEOUT_SECONDS)
            await self._gateway.stop_stream()
            stream_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await stream_task

        asyncio.run(run_stream_with_timeout())
        if len(all_ticks) == 0:
            self.skipTest("No ticks received. MetaTrader terminal may be offline.")
        assert all(isinstance(t, TickModel) for t in all_ticks), "All ticks should be TickModel"
        assert all_ticks[0].close_price > 0, f"Close price should be > 0, got {all_ticks[0].close_price}"
        assert all_ticks[0].bid_price > 0, f"Bid price should be > 0, got {all_ticks[0].bid_price}"
        assert all_ticks[0].ask_price > 0, f"Ask price should be > 0, got {all_ticks[0].ask_price}"
        assert all_ticks[0].date is not None, "Date should not be None"
        assert all_ticks[0].is_simulated is False, f"is_simulated should be False, got {all_ticks[0].is_simulated}"
        self._log.info(f"Received {len(all_ticks)} ticks for {self._SYMBOL}, last price: {all_ticks[-1].close_price}")
