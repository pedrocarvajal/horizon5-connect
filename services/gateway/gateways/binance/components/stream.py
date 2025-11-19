import datetime
import json
from collections.abc import Callable
from typing import Any, Dict, List

import websockets

from configs.timezone import TIMEZONE
from models.tick import TickModel
from services.gateway.gateways.binance.components.base import BaseComponent
from helpers.parse import parse_optional_float


class StreamComponent(BaseComponent):
    async def stream(
        self,
        streams: List[str],
        callback: Callable[[Any], None],
    ) -> None:
        if not streams:
            self._log.error("streams is required")
            return

        if not isinstance(streams, list):
            self._log.error("streams must be a list")
            return

        if len(streams) == 0:
            self._log.error("streams must not be empty")
            return

        for stream in streams:
            if not stream:
                self._log.error("stream item cannot be empty")
                return

            if not isinstance(stream, str):
                self._log.error("all stream items must be strings")
                return

        if not callback:
            self._log.error("callback is required")
            return

        if not callable(callback):
            self._log.error("callback must be callable")
            return

        stream_path = "/".join(streams)
        url = f"{self._config.fapi_ws_url}/{stream_path}"

        for stream in streams:
            if not any(stream.endswith(suffix) for suffix in ["bookTicker"]):
                self._log.error(f"Unsupported stream: {stream}")
                return

        async with websockets.connect(url) as websocket:
            async for message in websocket:
                try:
                    data = json.loads(message)

                except Exception as e:
                    self._log.error(f"Error processing message: {e}")
                    continue

                if data and data.get("e") == "bookTicker":
                    tick = self._adapt_tick_from_stream(response=data)
                    await callback(tick)
                else:
                    self._log.error(f"Unsupported event: {data.get('e')}")
                    continue

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _adapt_tick_from_stream(
        self,
        response: Dict[str, Any],
    ) -> TickModel:
        best_bid = parse_optional_float(value=response.get("b", 0.0))
        best_ask = parse_optional_float(value=response.get("a", 0.0))
        price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0.0

        return TickModel(
            sandbox=False,
            price=price,
            bid_price=best_bid,
            ask_price=best_ask,
            date=datetime.datetime.now(tz=TIMEZONE),
        )
