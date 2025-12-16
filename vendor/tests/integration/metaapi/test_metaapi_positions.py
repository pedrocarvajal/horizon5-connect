"""Integration tests for MetaAPI position operations."""

from vendor.enums.order_side import OrderSide
from vendor.services.gateway.models.gateway_position import GatewayPositionModel
from vendor.tests.integration.metaapi.wrappers.metaapi import MetaApiWrapper


class TestMetaApiPositions(MetaApiWrapper):
    """Integration tests for MetaAPI position retrieval."""

    def setUp(self) -> None:
        super().setUp()

    def test_get_positions(self) -> None:
        """Test retrieving all positions."""
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
            assert position.side in [
                OrderSide.BUY,
                OrderSide.SELL,
                None,
            ], "Side should be BUY, SELL, or None"
            assert position.volume != 0, "Volume should not be 0"
            assert position.open_price >= 0, "Open price should be >= 0"
            assert position.response is not None, "Response should not be None"
        self._log.info(f"Total positions found: {len(positions)}")

    def test_get_positions_by_symbol(self) -> None:
        """Test retrieving positions filtered by symbol."""
        self._log.info(f"Getting positions for {self._SYMBOL}")
        positions = self._gateway.get_positions(symbol=self._SYMBOL)
        assert positions is not None, "Positions should not be None"
        assert isinstance(positions, list), "Positions should be a list"
        assert all(isinstance(p, GatewayPositionModel) for p in positions), "Positions should be GatewayPositionModel"
        for position in positions:
            assert position.symbol.upper() == self._SYMBOL.upper(), f"Symbol should be {self._SYMBOL}"
        self._log.info(f"Total positions found for {self._SYMBOL}: {len(positions)}")
