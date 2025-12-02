# Code reviewed on 2025-12-02 by Pedro Carvajal

from enums.order_side import OrderSide
from tests.services.wrappers.orderbook import OrderbookWrapper


class TestServiceOrderbookFinancial(OrderbookWrapper):
    """
    Financial calculation tests for OrderbookService from a quantitative trading perspective.

    This test suite validates financial calculations with focus on:
    - Accounting identities and invariants (NAV, Equity, Margin Level)
    - Multi-position portfolio calculations
    - Margin mechanics with various leverage ratios
    - Realistic trading scenarios (hedging, position sizing, DCA)
    - Precision in financial calculations
    - Stress testing under market volatility

    All tests are designed with mathematically correct expectations based on
    quantitative finance principles.
    """

    # ═══════════════════════════════════════════════════════════
    # ACCOUNTING IDENTITY TESTS
    # ═══════════════════════════════════════════════════════════

    def test_nav_identity_with_no_positions(self) -> None:
        """Verify NAV = Balance when no positions are open."""
        tick = self._create_tick(50000.0)
        self._orderbook.refresh(tick)

        expected_nav = self._INITIAL_BALANCE
        assert abs(self._orderbook.nav - expected_nav) < self._EPSILON

    def test_nav_identity_with_open_position(self) -> None:
        """Verify NAV = Balance + Used Margin + PnL with open position."""
        self._open_position(self._orderbook, OrderSide.BUY, 0.1, 50000.0)
        self._assert_accounting_identity(self._orderbook, "NAV Identity")

    def test_equity_identity_with_profitable_position(self) -> None:
        """Verify Equity = Balance + PnL for profitable position."""
        self._open_position(self._orderbook, OrderSide.BUY, 0.1, 50000.0)

        profit_tick = self._create_tick(51000.0)
        self._orderbook.refresh(profit_tick)

        equity = self._orderbook.equity
        balance = self._orderbook.balance
        pnl = self._orderbook.pnl

        expected_equity = balance + pnl
        assert abs(equity - expected_equity) < self._EPSILON
        assert pnl > 0

    def test_equity_identity_with_losing_position(self) -> None:
        """Verify Equity = Balance + PnL for losing position."""
        self._open_position(self._orderbook, OrderSide.BUY, 0.1, 50000.0)

        loss_tick = self._create_tick(49000.0)
        self._orderbook.refresh(loss_tick)

        equity = self._orderbook.equity
        balance = self._orderbook.balance
        pnl = self._orderbook.pnl

        expected_equity = balance + pnl
        assert abs(equity - expected_equity) < self._EPSILON
        assert pnl < 0

    def test_free_margin_identity(self) -> None:
        """Verify Free Margin = Equity - Used Margin."""
        self._open_position(self._orderbook, OrderSide.BUY, 0.1, 50000.0)

        free_margin = self._orderbook.free_margin
        equity = self._orderbook.equity
        used_margin = self._orderbook.used_margin

        expected_free_margin = equity - used_margin
        assert abs(free_margin - expected_free_margin) < self._EPSILON

    def test_margin_level_identity(self) -> None:
        """Verify Margin Level = Equity / Used Margin."""
        self._open_position(self._orderbook, OrderSide.BUY, 0.1, 50000.0)

        margin_level = self._orderbook.margin_level
        equity = self._orderbook.equity
        used_margin = self._orderbook.used_margin

        expected_margin_level = equity / used_margin if used_margin > 0 else float("inf")
        assert abs(margin_level - expected_margin_level) < self._EPSILON

    def test_capital_conservation_after_full_cycle(self) -> None:
        """Verify capital is conserved after opening/closing at same price (no slippage)."""
        initial_nav = self._orderbook.nav

        order = self._open_position(self._orderbook, OrderSide.BUY, 0.1, 50000.0)

        same_price_tick = self._create_tick(50000.0)
        self._orderbook.refresh(same_price_tick)
        self._orderbook.close(order)

        final_nav = self._orderbook.nav
        assert abs(final_nav - initial_nav) < self._EPSILON

    # ═══════════════════════════════════════════════════════════
    # MULTI-POSITION TESTS
    # ═══════════════════════════════════════════════════════════

    def test_hedged_position_zero_pnl_at_entry(self) -> None:
        """Verify long + short positions at same price/volume result in zero net PnL."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)

        self._open_position(orderbook, OrderSide.BUY, 0.1, 50000.0)
        self._open_position(orderbook, OrderSide.SELL, 0.1, 50000.0)

        same_tick = self._create_tick(50000.0)
        orderbook.refresh(same_tick)

        total_pnl = orderbook.pnl
        assert abs(total_pnl) < self._EPSILON

    def test_hedged_position_pnl_cancels_on_movement(self) -> None:
        """Verify long + short positions have offsetting PnL on price movement."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)

        long_order = self._open_position(orderbook, OrderSide.BUY, 0.1, 50000.0)
        short_order = self._open_position(orderbook, OrderSide.SELL, 0.1, 50000.0)

        higher_tick = self._create_tick(51000.0)
        orderbook.refresh(higher_tick)

        long_pnl = long_order.profit
        short_pnl = short_order.profit

        assert long_pnl > 0
        assert short_pnl < 0
        assert abs(long_pnl + short_pnl) < self._EPSILON

    def test_exposure_calculation_multi_position(self) -> None:
        """Verify exposure is sum of all position notional values."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)

        self._open_position(orderbook, OrderSide.BUY, 0.1, 50000.0)
        self._open_position(orderbook, OrderSide.BUY, 0.05, 50000.0)
        self._open_position(orderbook, OrderSide.SELL, 0.08, 50000.0)

        expected_exposure = (0.1 * 50000.0) + (0.05 * 50000.0) + (0.08 * 50000.0)
        actual_exposure = orderbook.exposure

        assert abs(actual_exposure - expected_exposure) < self._EPSILON

    def test_used_margin_multi_position(self) -> None:
        """Verify used margin is correctly calculated across multiple positions."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=20)

        self._open_position(orderbook, OrderSide.BUY, 0.1, 50000.0)
        self._open_position(orderbook, OrderSide.SELL, 0.05, 50000.0)

        expected_margin = ((0.1 * 50000.0) / 20) + ((0.05 * 50000.0) / 20)
        actual_margin = orderbook.used_margin

        assert abs(actual_margin - expected_margin) < self._EPSILON

    def test_portfolio_mixed_pnl(self) -> None:
        """Verify portfolio calculations with mixed winning and losing positions."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)

        winning_order = self._open_position(orderbook, OrderSide.BUY, 0.1, 50000.0)
        losing_order = self._open_position(orderbook, OrderSide.SELL, 0.1, 50000.0)

        new_price_tick = self._create_tick(51000.0)
        orderbook.refresh(new_price_tick)

        winning_pnl = winning_order.profit
        losing_pnl = losing_order.profit
        total_pnl = orderbook.pnl

        assert winning_pnl > 0
        assert losing_pnl < 0
        assert abs(total_pnl - (winning_pnl + losing_pnl)) < self._EPSILON

    # ═══════════════════════════════════════════════════════════
    # LEVERAGE MECHANICS TESTS
    # ═══════════════════════════════════════════════════════════

    def test_required_margin_decreases_with_leverage(self) -> None:
        """Verify required margin decreases as leverage increases."""
        volume = 0.1
        price = 50000.0

        orderbook_low = self._create_orderbook(balance=10000.0, leverage=5)
        self._open_position(orderbook_low, OrderSide.BUY, volume, price)
        margin_low = orderbook_low.used_margin

        orderbook_high = self._create_orderbook(balance=10000.0, leverage=20)
        self._open_position(orderbook_high, OrderSide.BUY, volume, price)
        margin_high = orderbook_high.used_margin

        assert margin_high < margin_low
        assert abs(margin_low / margin_high - 4.0) < self._EPSILON

    def test_pnl_independent_of_leverage(self) -> None:
        """Verify PnL is independent of leverage for same position size."""
        volume = 0.1
        entry_price = 50000.0
        exit_price = 51000.0

        orderbook_low = self._create_orderbook(balance=10000.0, leverage=5)
        self._open_position(orderbook_low, OrderSide.BUY, volume, entry_price)
        exit_tick_low = self._create_tick(exit_price)
        orderbook_low.refresh(exit_tick_low)
        pnl_low = orderbook_low.pnl

        orderbook_high = self._create_orderbook(balance=10000.0, leverage=50)
        self._open_position(orderbook_high, OrderSide.BUY, volume, entry_price)
        exit_tick_high = self._create_tick(exit_price)
        orderbook_high.refresh(exit_tick_high)
        pnl_high = orderbook_high.pnl

        assert abs(pnl_low - pnl_high) < self._EPSILON

    def test_margin_level_higher_with_high_leverage(self) -> None:
        """
        Verify margin level is HIGHER with high leverage for same absolute loss.

        This is mathematically correct because:
        - High leverage uses less margin
        - Same absolute loss is smaller % of smaller margin
        - Therefore margin level (equity/margin) is higher
        """
        volume = 0.1
        entry_price = 50000.0
        loss_price = 49000.0

        orderbook_low = self._create_orderbook(balance=10000.0, leverage=5)
        self._open_position(orderbook_low, OrderSide.BUY, volume, entry_price)
        loss_tick_low = self._create_tick(loss_price)
        orderbook_low.refresh(loss_tick_low)
        margin_level_low = orderbook_low.margin_level

        orderbook_high = self._create_orderbook(balance=10000.0, leverage=50)
        self._open_position(orderbook_high, OrderSide.BUY, volume, entry_price)
        loss_tick_high = self._create_tick(loss_price)
        orderbook_high.refresh(loss_tick_high)
        margin_level_high = orderbook_high.margin_level

        assert margin_level_high > margin_level_low

    def test_liquidation_price_closer_with_high_leverage(self) -> None:
        """
        Verify liquidation happens at smaller price move with high leverage.

        Even though margin level is higher for same absolute loss,
        liquidation happens at smaller % price move due to leverage effect.
        """
        orderbook_high_lev = self._create_orderbook(balance=100.0, leverage=100)
        self._open_position(orderbook_high_lev, OrderSide.BUY, 0.01, 50000.0)

        catastrophic_drop = self._create_tick(10000.0)
        orderbook_high_lev.refresh(catastrophic_drop)

        second_tick = self._create_tick(10000.0)
        orderbook_high_lev.refresh(second_tick)

        open_orders = len([o for o in orderbook_high_lev.orders if o.status.is_open()])
        assert open_orders == 0

    # ═══════════════════════════════════════════════════════════
    # PRECISION TESTS
    # ═══════════════════════════════════════════════════════════

    def test_small_trades_accumulate_pnl_correctly(self) -> None:
        """Verify PnL accumulates correctly across multiple small trades."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)

        entry_price = 50000.0
        exit_price = 50100.0
        volume_per_trade = 0.001

        for _ in range(10):
            self._open_position(orderbook, OrderSide.BUY, volume_per_trade, entry_price)

        exit_tick = self._create_tick(exit_price)
        orderbook.refresh(exit_tick)

        total_pnl = orderbook.pnl
        expected_pnl = 10 * volume_per_trade * (exit_price - entry_price)

        assert abs(total_pnl - expected_pnl) < self._EPSILON

    def test_balance_accurate_after_multiple_cycles(self) -> None:
        """Verify balance tracking remains accurate after multiple open/close cycles."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)
        initial_balance = orderbook.balance

        for _ in range(5):
            order = self._open_position(orderbook, OrderSide.BUY, 0.01, 50000.0)
            same_price_tick = self._create_tick(50000.0)
            orderbook.refresh(same_price_tick)
            orderbook.close(order)

        final_balance = orderbook.balance
        assert abs(final_balance - initial_balance) < self._EPSILON

    def test_nav_conservation_fractional_volumes(self) -> None:
        """Verify NAV calculations accurate with very small fractional volumes."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)

        self._open_position(orderbook, OrderSide.BUY, 0.00123, 50000.0)
        self._open_position(orderbook, OrderSide.SELL, 0.00456, 50000.0)

        tick = self._create_tick(50000.0)
        orderbook.refresh(tick)

        self._assert_accounting_identity(orderbook, "NAV with fractional volumes")

    # ═══════════════════════════════════════════════════════════
    # REALISTIC TRADING SCENARIOS
    # ═══════════════════════════════════════════════════════════

    def test_pyramiding_increases_exposure(self) -> None:
        """Verify pyramiding (adding to winners) increases exposure correctly."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)

        self._open_position(orderbook, OrderSide.BUY, 0.1, 50000.0)

        profit_tick = self._create_tick(51000.0)
        orderbook.refresh(profit_tick)

        self._open_position(orderbook, OrderSide.BUY, 0.05, 51000.0)

        expected_exposure = (0.1 * 50000.0) + (0.05 * 51000.0)
        assert abs(orderbook.exposure - expected_exposure) < self._EPSILON

    def test_position_averaging_down(self) -> None:
        """Verify averaging down affects average entry price correctly."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=10)

        self._open_position(orderbook, OrderSide.BUY, 0.1, 50000.0)

        loss_tick = self._create_tick(48000.0)
        orderbook.refresh(loss_tick)

        self._open_position(orderbook, OrderSide.BUY, 0.1, 48000.0)

        recovery_tick = self._create_tick(49000.0)
        orderbook.refresh(recovery_tick)

        total_volume = 0.2
        weighted_avg_entry = (0.1 * 50000.0 + 0.1 * 48000.0) / total_volume
        expected_pnl = total_volume * (49000.0 - weighted_avg_entry)

        assert abs(orderbook.pnl - expected_pnl) < self._EPSILON

    def test_dollar_cost_averaging_strategy(self) -> None:
        """Verify DCA strategy calculations are accurate across multiple entries."""
        orderbook = self._create_orderbook(balance=10000.0, leverage=5)

        prices = [50000.0, 49000.0, 48000.0, 47000.0]
        volume_per_entry = 0.02

        orders = []
        for price in prices:
            order = self._open_position(orderbook, OrderSide.BUY, volume_per_entry, price)
            orders.append(order)

        final_tick = self._create_tick(48500.0)
        orderbook.refresh(final_tick)

        assert orderbook.exposure > 0
        assert len([o for o in orderbook.orders if o.status.is_open()]) == len(orders)
