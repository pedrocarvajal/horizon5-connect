# horizon-connect

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey.svg)
![Version](https://img.shields.io/badge/version-0.1.0-green.svg)
![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-orange.svg)

## Roadmap

### Core Infrastructure

|                                                                                                           | Status        | Version |
| --------------------------------------------------------------------------------------------------------- | ------------- | ------- |
| Alpha release: Basic framework architecture for strategy composition and backtesting with Binance gateway | _in-progress_ | 0.1.0   |

### Performance Analysis & Reporting

|                                                                                                                              | Status | Version |
| ---------------------------------------------------------------------------------------------------------------------------- | ------ | ------- |
| Backtest report generation: PDF reports with performance metrics, equity curves, drawdown analysis, and trade statistics     |        | 0.2.0   |
| Risk metrics calculation: Sharpe ratio, Sortino ratio, Calmar ratio, maximum drawdown, volatility, and risk-adjusted returns |        | 0.2.1   |
| Performance attribution: Trade-by-trade analysis, win rate, profit factor, and expectancy metrics                            |        | 0.2.2   |

### Strategy Optimization

|                                                                                                           | Status | Version |
| --------------------------------------------------------------------------------------------------------- | ------ | ------- |
| Parameter optimization engine: Grid search and brute force optimization for strategy parameters           |        | 0.3.0   |
| Walk-forward analysis: Out-of-sample testing with rolling window optimization                             |        | 0.3.1   |
| Multi-objective optimization: Simultaneous optimization of risk-adjusted returns and drawdown constraints |        | 0.3.2   |

### Production Trading

|                                                                                        | Status | Version |
| -------------------------------------------------------------------------------------- | ------ | ------- |
| Live trading mode: Deploy backtested strategies to production with Binance gateway     |        | 0.4.0   |
| Order management system: Position sizing, risk limits, and order execution monitoring  |        | 0.4.1   |
| Real-time performance tracking: Live P&L, position tracking, and performance dashboard |        | 0.4.2   |

### Risk Management & Stress Testing

|                                                                                                                    | Status | Version |
| ------------------------------------------------------------------------------------------------------------------ | ------ | ------- |
| Monte Carlo simulation: Statistical robustness testing with multiple simulated scenarios                           |        |         |
| Regime detection: Market condition identification (trending, ranging, high/low volatility regimes)                 |        |         |
| Stress testing framework: Strategy resilience under volatility shocks, regime changes, and market stress scenarios |        |         |
| Portfolio-level risk metrics: Correlation analysis, portfolio VaR, and diversification metrics                     |        |         |

### Multi-Asset & Multi-Strategy Portfolio

|                                                                                                     | Status | Version |
| --------------------------------------------------------------------------------------------------- | ------ | ------- |
| Multi-asset support: Extend gateway integration to MetaTrader 5 (MetaAPI) for forex and CFD trading |        |         |
| Portfolio construction: Multi-strategy portfolio allocation with risk parity and optimization       |        |         |
| Cross-asset correlation analysis: Portfolio-level risk management across crypto and forex markets   |        |         |
| Dynamic position sizing: Kelly criterion, fixed fractional, and volatility-based position sizing    |        |         |

---

**Note:**
What we are looking for is a framework where you build a full portfolio (not just one strategy, multi assets multi strategy) easily, backtest, optimize and go to production quickly.
A framework that is open to the complete quantitative finance workflow.
