from typing import Any, Dict, List, Optional

from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.helpers import has_api_error, parse_optional_float
from services.gateway.models.gateway_account import (
    GatewayAccountBalanceModel,
    GatewayAccountModel,
)


class AccountComponent(BaseComponent):
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
