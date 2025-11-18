# Last coding review: 2025-11-18 13:40:00

import asyncio
from typing import List

from models.tick import TickModel
from tests.integration.wrappers.binance import BinanceWrapper


class TestBinanceStream(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_stream")

    def test_stream(self) -> None:
        self._log.info("Testing stream connection for BTCUSDT")

        all_ticks: List[TickModel] = []

        async def callback(tick: TickModel) -> None:
            self._log.info(f"Received tick: price={tick.price}, bid={tick.bid_price}, ask={tick.ask_price}")
            all_ticks.append(tick)

        async def run_stream() -> None:
            await self._gateway.stream(
                streams=["btcusdt@bookTicker"],
                callback=callback,
            )

        async def test_with_timeout() -> None:
            stream_task = asyncio.create_task(run_stream())
            await asyncio.sleep(5)
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass

        asyncio.run(test_with_timeout())

        assert len(all_ticks) > 0, f"Should receive at least 1 tick, got {len(all_ticks)}"
        assert all(isinstance(t, TickModel) for t in all_ticks), "All ticks should be TickModel"
        assert all_ticks[0].price > 0, f"Price should be > 0, got {all_ticks[0].price}"
        assert all_ticks[0].bid_price > 0, f"Bid price should be > 0, got {all_ticks[0].bid_price}"
        assert all_ticks[0].ask_price > 0, f"Ask price should be > 0, got {all_ticks[0].ask_price}"
        assert all_ticks[0].date is not None, "Date should not be None"
        assert all_ticks[0].sandbox is False, f"Sandbox should be False, got {all_ticks[0].sandbox}"

        self._log.info(f"Total ticks received: {len(all_ticks)}")
