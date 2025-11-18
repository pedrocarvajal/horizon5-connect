from typing import Any, Dict, List, Optional

from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.gateways.binance.components.position import PositionComponent
from services.gateway.gateways.binance.components.symbol import SymbolComponent
from services.gateway.helpers import has_api_error, parse_optional_float
from services.gateway.models.gateway_account import (
    GatewayAccountBalanceModel,
    GatewayAccountModel,
)


class AccountComponent(BaseComponent):
    _position_component: PositionComponent
    _symbol_component: SymbolComponent

    def __init__(
        self,
        config: Any,
    ) -> None:
        super().__init__(config)

        self._position_component = PositionComponent(
            config=config,
        )

        self._symbol_component = SymbolComponent(
            config=config,
        )

    def get_account(
        self,
        **kwargs: Any,  # noqa: ARG002
    ) -> Optional[GatewayAccountModel]:
        url = f"{self._config.fapi_v2_url}/account"

        response = self._execute(
            method="GET",
            url=url,
            params=None,
        )

        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)

        if has_error:
            self._log.error(f"Failed to get account info: {error_msg} (code: {error_code})")
            return None

        return self._adapt_account_response(
            response=response,
        )

    def get_verification(
        self,
        symbol: str = "BTCUSDT",
    ) -> Dict[str, bool]:
        return {
            "required_leverage": self._check_leverage(symbol=symbol),
            "usdt_balance": self._check_usdt_balance(),
            "cross_margin": self._check_cross_margin(),
            "one_way_mode": self._check_one_way_mode(),
            "trading_permissions": self._check_trading_permissions(),
        }

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _adapt_account_response(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewayAccountModel]:
        balances: List[GatewayAccountBalanceModel] = []

        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(
            response=response,
        )

        if has_error:
            self._log.error(f"API Error: {error_msg} (code: {error_code})")
            return None

        assets = response.get("assets", [])

        for asset_data in assets:
            wallet_balance = parse_optional_float(value=asset_data.get("walletBalance", 0))
            locked_balance = parse_optional_float(value=asset_data.get("locked", 0))

            balances.append(
                GatewayAccountBalanceModel(
                    asset=asset_data.get("asset", ""),
                    balance=wallet_balance,
                    locked=locked_balance,
                    response=asset_data,
                )
            )

        total_wallet_balance = parse_optional_float(value=response.get("totalWalletBalance", 0))
        total_margin_balance = parse_optional_float(value=response.get("totalMarginBalance", 0))
        total_unrealized_pnl = parse_optional_float(value=response.get("totalUnrealizedProfit", 0))
        total_position_initial_margin = parse_optional_float(value=response.get("totalPositionInitialMargin", 0))
        total_open_order_initial_margin = parse_optional_float(value=response.get("totalOpenOrderInitialMargin", 0))

        return GatewayAccountModel(
            balances=balances,
            balance=total_wallet_balance,
            nav=total_margin_balance,
            locked=total_open_order_initial_margin,
            margin=total_position_initial_margin,
            exposure=total_position_initial_margin,
            pnl=total_unrealized_pnl,
            response=response,
        )

    def _check_leverage(
        self,
        symbol: str,
    ) -> bool:
        leverage_info = self._symbol_component.get_leverage_info(
            symbol=symbol,
        )

        if leverage_info:
            return leverage_info.leverage >= 1

        return False

    def _check_usdt_balance(
        self,
    ) -> bool:
        account = self.get_account()

        if account:
            for balance in account.balances:
                if balance.asset == "USDT":
                    return balance.balance > 0

        return False

    def _check_cross_margin(
        self,
    ) -> bool:
        positions = self._position_component.get_positions()

        if positions:
            margin_types = set()

            for position in positions:
                margin_type = position.response.get("marginType", "")

                if margin_type:
                    margin_types.add(margin_type.lower())

            return "cross" in margin_types and len(margin_types) == 1
        return True

    def _check_one_way_mode(
        self,
    ) -> bool:
        position_mode = self._position_component.get_position_mode()
        if position_mode is not None:
            return not position_mode
        return False

    def _check_trading_permissions(
        self,
    ) -> bool:
        account = self.get_account()

        if account and account.response:
            return account.response.get("canTrade", False)

        return False
