# Last coding review: 2025-11-18 13:45:00

from enums.order_side import OrderSide
from services.gateway.models.gateway_position import GatewayPositionModel
from tests.integration.binance.wrappers.binance import BinanceWrapper


class TestBinancePositions(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_positions")

    def test_get_positions(self) -> None:
        self._log.info("Getting all positions")

        positions = self._gateway.get_positions()

        assert positions is not None, "Positions should not be None"
        assert isinstance(positions, list), "Positions should be a list"
        assert all(isinstance(p, GatewayPositionModel) for p in positions), (
            "All positions should be GatewayPositionModel"
        )

        if len(positions) > 0:
            position = positions[0]
            assert position.symbol != "", "Symbol should not be empty"
            assert position.side in [OrderSide.BUY, OrderSide.SELL, None], "Side should be BUY, SELL, or None"
            assert position.volume != 0, "Volume should not be 0"
            assert position.open_price >= 0, "Open price should be >= 0"
            assert position.response is not None, "Response should not be None"

        self._log.info(f"Total positions found: {len(positions)}")

    def test_get_positions_by_symbol(self) -> None:
        self._log.info("Getting positions for BTCUSDT")

        positions = self._gateway.get_positions(symbol="BTCUSDT")

        assert positions is not None, "Positions should not be None"
        assert isinstance(positions, list), "Positions should be a list"
        assert all(isinstance(p, GatewayPositionModel) for p in positions), "Positions should be GatewayPositionModel"

        for position in positions:
            assert position.symbol == "BTCUSDT", "Symbol should be BTCUSDT"

        self._log.info(f"Total positions found for BTCUSDT: {len(positions)}")
