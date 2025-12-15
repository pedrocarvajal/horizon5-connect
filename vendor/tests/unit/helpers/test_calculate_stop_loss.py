import unittest

from vendor.enums.order_side import OrderSide
from vendor.enums.tp_sl_method import TpSlMethod
from vendor.helpers.calculate_stop_loss import calculate_stop_loss


class TestCalculateStopLoss(unittest.TestCase):
    _ENTRY_PRICE: float = 100.0
    _PERCENTAGE_VALUE: float = 0.05
    _ATR_VALUE: float = 2.0
    _ATR_MULTIPLIER: float = 1.5
    _FIXED_VALUE: float = 5.0

    def test_calculate_stop_loss_percentage_buy_returns_lower_price(self) -> None:
        result = calculate_stop_loss(
            entry_price=self._ENTRY_PRICE,
            value=self._PERCENTAGE_VALUE,
            method=TpSlMethod.PERCENTAGE,
            side=OrderSide.BUY,
        )

        assert result == 95.0

    def test_calculate_stop_loss_percentage_sell_returns_higher_price(self) -> None:
        result = calculate_stop_loss(
            entry_price=self._ENTRY_PRICE,
            value=self._PERCENTAGE_VALUE,
            method=TpSlMethod.PERCENTAGE,
            side=OrderSide.SELL,
        )

        assert result == 105.0

    def test_calculate_stop_loss_atr_buy_returns_lower_price(self) -> None:
        result = calculate_stop_loss(
            entry_price=self._ENTRY_PRICE,
            value=self._ATR_MULTIPLIER,
            method=TpSlMethod.ATR,
            side=OrderSide.BUY,
            atr_value=self._ATR_VALUE,
        )

        assert result == 97.0

    def test_calculate_stop_loss_atr_sell_returns_higher_price(self) -> None:
        result = calculate_stop_loss(
            entry_price=self._ENTRY_PRICE,
            value=self._ATR_MULTIPLIER,
            method=TpSlMethod.ATR,
            side=OrderSide.SELL,
            atr_value=self._ATR_VALUE,
        )

        assert result == 103.0

    def test_calculate_stop_loss_atr_without_atr_value_raises_error(self) -> None:
        with self.assertRaises(ValueError) as context:
            calculate_stop_loss(
                entry_price=self._ENTRY_PRICE,
                value=self._ATR_MULTIPLIER,
                method=TpSlMethod.ATR,
                side=OrderSide.BUY,
                atr_value=None,
            )

        assert "atr_value is required" in str(context.exception)

    def test_calculate_stop_loss_fixed_buy_returns_lower_price(self) -> None:
        result = calculate_stop_loss(
            entry_price=self._ENTRY_PRICE,
            value=self._FIXED_VALUE,
            method=TpSlMethod.FIXED,
            side=OrderSide.BUY,
        )

        assert result == 95.0

    def test_calculate_stop_loss_fixed_sell_returns_higher_price(self) -> None:
        result = calculate_stop_loss(
            entry_price=self._ENTRY_PRICE,
            value=self._FIXED_VALUE,
            method=TpSlMethod.FIXED,
            side=OrderSide.SELL,
        )

        assert result == 105.0

    def test_calculate_stop_loss_with_zero_value_returns_entry_price(self) -> None:
        test_cases = [
            (TpSlMethod.PERCENTAGE, OrderSide.BUY),
            (TpSlMethod.PERCENTAGE, OrderSide.SELL),
            (TpSlMethod.FIXED, OrderSide.BUY),
            (TpSlMethod.FIXED, OrderSide.SELL),
        ]

        for method, side in test_cases:
            with self.subTest(method=method, side=side):
                result = calculate_stop_loss(
                    entry_price=self._ENTRY_PRICE,
                    value=0.0,
                    method=method,
                    side=side,
                )

                assert result == self._ENTRY_PRICE
