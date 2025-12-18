"""Propfirm optimization script for EMA5 Breakout strategy."""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

TOTAL_COMPLIANCE_CHECKS = 4

PORTFOLIO_TEMPLATE = '''"""Propfirm test portfolio - isolated EMA5 Breakout strategy for optimization."""

from strategies.ema5_breakout import EMA5BreakoutStrategy
from vendor.enums.asset_quality_method import AssetQualityMethod
from vendor.enums.tp_sl_method import TpSlMethod
from vendor.interfaces.strategy import StrategyInterface
from vendor.services.asset import AssetService
from vendor.services.portfolio import PortfolioService
from typing import List


class Asset(AssetService):
    """XAUUSD asset with only EMA5 Breakout for propfirm testing."""

    _symbol = "XAUUSD"
    _gateway_name = "metaapi"
    _asset_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE
    _strategies: List[StrategyInterface]

    def __init__(self, allocation: float = 0.0, enabled: bool = True, leverage: int = 100) -> None:
        super().__init__(allocation=allocation, enabled=enabled, leverage=leverage)
        self._setup_strategies()
        self._setup_allocation()

    def _setup_strategies(self) -> None:
        self._strategies = [
            EMA5BreakoutStrategy(
                id="ema5_breakout",
                allocation=0.0,
                enabled=True,
                settings={{
                    "entry_allow_multiple": False,
                    "entry_waiting_time": 0,
                    "entry_volume": {entry_volume},
                    "entry_ema_period": 5,
                    "main_take_profit": {main_tp},
                    "main_take_profit_method": TpSlMethod.FIXED,
                    "main_stop_loss": {main_sl},
                    "main_stop_loss_method": TpSlMethod.FIXED,
                    "recovery_enabled": {recovery_enabled},
                    "recovery_maximum_layers": {recovery_layers},
                    "recovery_stop_loss": {recovery_sl},
                    "recovery_stop_loss_method": TpSlMethod.FIXED,
                    "recovery_take_profit": {recovery_tp},
                    "recovery_take_profit_method": TpSlMethod.FIXED,
                }},
            ),
        ]

    def _setup_allocation(self) -> None:
        enabled_strategies = [s for s in self._strategies if s.enabled]
        allocation_per_strategy = self.allocation / max(len(enabled_strategies), 1)
        for strategy in enabled_strategies:
            strategy.allocation = allocation_per_strategy


class Portfolio(PortfolioService):
    """Propfirm test portfolio for EMA5 Breakout optimization."""

    _id = "propfirm-test"
    _portfolio_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE

    def __init__(self) -> None:
        super().__init__()
        self.setup_assets()

    def setup_assets(self) -> None:
        self._assets = [
            {{
                "asset": Asset,
                "allocation": 100_000,
                "enabled": True,
            }},
        ]
'''


def run_backtest(config: Dict[str, Any]) -> Dict[str, Any]:
    """Run backtest with given configuration and return metrics."""
    portfolio_content = PORTFOLIO_TEMPLATE.format(
        entry_volume=config["entry_volume"],
        main_tp=config["main_tp"],
        main_sl=config["main_sl"],
        recovery_enabled=config["recovery_enabled"],
        recovery_layers=config["recovery_layers"],
        recovery_sl=config["recovery_sl"],
        recovery_tp=config["recovery_tp"],
    )

    with Path("portfolios/propfirm-test.py").open("w") as f:
        f.write(portfolio_content)

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "backtest.py",
            "--portfolio-path",
            "portfolios/propfirm-test.py",
            "--from-date",
            "2019-01-01",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=600,
    )

    output = result.stdout + result.stderr
    output_clean = re.sub(r"\x1b\[[0-9;]*m", "", output)

    start = output_clean.find("{")
    if start == -1:
        return {"error": "No JSON found"}

    brace_count = 0
    end = start
    for i, c in enumerate(output_clean[start:], start):
        if c == "{":
            brace_count += 1
        elif c == "}":
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break

    try:
        data = json.loads(output_clean[start:end])
        strategy_data = data.get("assets", {}).get("XAUUSD", {}).get("strategies", {}).get("ema5_breakout", {})

        return {
            "config": config,
            "performance_%": round(strategy_data.get("performance_percentage", 0) * 100, 2),
            "max_dd_%": round(strategy_data.get("performance_max_drawdown", 0) * 100, 2),
            "win_ratio_%": round(strategy_data.get("trade_win_ratio", 0) * 100, 1),
            "total_orders": strategy_data.get("trade_total_orders", 0),
            "profit_factor": round(strategy_data.get("trade_profit_factor", 0), 2),
            "propfirm_score_%": round(strategy_data.get("score_quality_propfirm", 0) * 100, 1),
            "daily_loss_compliant": strategy_data.get("propfirm_daily_loss_compliant", False),
            "overall_loss_compliant": strategy_data.get("propfirm_overall_loss_compliant", False),
            "consistency_compliant": strategy_data.get("propfirm_consistency_compliant", False),
            "trading_days_compliant": strategy_data.get("propfirm_trading_days_compliant", False),
            "max_daily_loss_%": round(strategy_data.get("risk_max_daily_loss", 0) * 100, 2),
            "best_day_ratio_%": round(strategy_data.get("propfirm_best_day_profit_ratio", 0) * 100, 1),
        }
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}"}


def print_result(result: Dict[str, Any], test_name: str) -> None:
    """Print formatted result."""
    if "error" in result:
        print(f"[{test_name}] ERROR: {result['error']}")  # noqa: T201
        return

    compliant_count = sum(
        [
            result["daily_loss_compliant"],
            result["overall_loss_compliant"],
            result["consistency_compliant"],
            result["trading_days_compliant"],
        ]
    )

    total = TOTAL_COMPLIANCE_CHECKS
    status = "READY" if compliant_count == total else f"NOT READY ({compliant_count}/{total})"

    config = result["config"]
    volume = config["entry_volume"]
    recovery = config["recovery_enabled"]
    layers = config["recovery_layers"]
    main_sl = config["main_sl"]
    main_tp = config["main_tp"]

    print(f"""
{"=" * 80}
TEST: {test_name}
{"=" * 80}
Config: volume={volume}, recovery={recovery}, layers={layers}
        main_sl={main_sl}, main_tp={main_tp}

PROPFIRM STATUS: {status}
Score: {result["propfirm_score_%"]}%  |  Return: {result["performance_%"]}%  |  Max DD: {result["max_dd_%"]}%

COMPLIANCE:
  Daily Loss (<5%):    {"PASS" if result["daily_loss_compliant"] else "FAIL"} (worst: {result["max_daily_loss_%"]}%)
  Overall Loss (<10%): {"PASS" if result["overall_loss_compliant"] else "FAIL"} (max DD: {result["max_dd_%"]}%)
  Consistency (<30%):  {"PASS" if result["consistency_compliant"] else "FAIL"} (best day: {result["best_day_ratio_%"]}%)
  Trading Days (>4):   {"PASS" if result["trading_days_compliant"] else "FAIL"}

PERFORMANCE:
  Orders: {result["total_orders"]}  |  Win Ratio: {result["win_ratio_%"]}%  |  Profit Factor: {result["profit_factor"]}
""")  # noqa: T201


if __name__ == "__main__":
    configs = [
        {
            "name": "BASELINE (current)",
            "entry_volume": 0.25,
            "main_tp": 3,
            "main_sl": 15,
            "recovery_enabled": "True",
            "recovery_layers": 3,
            "recovery_sl": 15,
            "recovery_tp": 5,
        },
        {
            "name": "TEST 1: Reduced volume (0.15)",
            "entry_volume": 0.15,
            "main_tp": 3,
            "main_sl": 15,
            "recovery_enabled": "True",
            "recovery_layers": 3,
            "recovery_sl": 15,
            "recovery_tp": 5,
        },
        {
            "name": "TEST 2: Recovery disabled",
            "entry_volume": 0.25,
            "main_tp": 3,
            "main_sl": 15,
            "recovery_enabled": "False",
            "recovery_layers": 3,
            "recovery_sl": 15,
            "recovery_tp": 5,
        },
        {
            "name": "TEST 3: Recovery layers=2",
            "entry_volume": 0.25,
            "main_tp": 3,
            "main_sl": 15,
            "recovery_enabled": "True",
            "recovery_layers": 2,
            "recovery_sl": 15,
            "recovery_tp": 5,
        },
        {
            "name": "TEST 4: Tighter SL (10)",
            "entry_volume": 0.25,
            "main_tp": 3,
            "main_sl": 10,
            "recovery_enabled": "True",
            "recovery_layers": 3,
            "recovery_sl": 10,
            "recovery_tp": 5,
        },
        {
            "name": "TEST 5: Volume 0.15 + Recovery disabled",
            "entry_volume": 0.15,
            "main_tp": 3,
            "main_sl": 15,
            "recovery_enabled": "False",
            "recovery_layers": 3,
            "recovery_sl": 15,
            "recovery_tp": 5,
        },
    ]

    if len(sys.argv) > 1:
        test_index = int(sys.argv[1])
        configs = [configs[test_index]]

    print("=" * 80)  # noqa: T201
    print("PROPFIRM OPTIMIZATION - EMA5 BREAKOUT")  # noqa: T201
    print("=" * 80)  # noqa: T201

    results = []
    for config in configs:
        name = config.pop("name")
        print(f"\nRunning: {name}...")  # noqa: T201
        result = run_backtest(config)
        config["name"] = name
        result["name"] = name
        results.append(result)
        print_result(result, name)

    print("\n" + "=" * 80)  # noqa: T201
    print("SUMMARY - Sorted by Propfirm Score")  # noqa: T201
    print("=" * 80)  # noqa: T201

    valid_results = [r for r in results if "error" not in r]
    valid_results.sort(key=lambda x: x["propfirm_score_%"], reverse=True)

    for r in valid_results:
        compliant = sum(
            [
                r["daily_loss_compliant"],
                r["overall_loss_compliant"],
                r["consistency_compliant"],
                r["trading_days_compliant"],
            ]
        )
        total = TOTAL_COMPLIANCE_CHECKS
        name = r["name"]
        score = r["propfirm_score_%"]
        drawdown = r["max_dd_%"]
        print(f"{name:40} | Score: {score:5.1f}% | DD: {drawdown:6.2f}% | Compliance: {compliant}/{total}")  # noqa: T201
