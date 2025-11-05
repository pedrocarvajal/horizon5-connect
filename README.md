# horizon-connect

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey.svg)
![Version](https://img.shields.io/badge/version-0.1.0-green.svg)
![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-orange.svg)

## Roadmap

### Core Infrastructure

| Objective                                                                                                 | Status        | Version |
| --------------------------------------------------------------------------------------------------------- | ------------- | ------- |
| Alpha release: Basic framework architecture for strategy composition and backtesting with Binance gateway | _in-progress_ | 0.1.0   |

### Performance Analysis & Reporting

| Objective                                                                                                                    | Status | Version |
| ---------------------------------------------------------------------------------------------------------------------------- | ------ | ------- |
| Backtest report generation: PDF reports with performance metrics, equity curves, drawdown analysis, and trade statistics     |        | 0.2.0   |
| Risk metrics calculation: Sharpe ratio, Sortino ratio, Calmar ratio, maximum drawdown, volatility, and risk-adjusted returns |        | 0.2.1   |
| Performance attribution: Trade-by-trade analysis, win rate, profit factor, and expectancy metrics                            |        | 0.2.2   |

### Strategy Optimization

| Objective                                                                                                 | Status | Version |
| --------------------------------------------------------------------------------------------------------- | ------ | ------- |
| Parameter optimization engine: Grid search and brute force optimization for strategy parameters           |        | 0.3.0   |
| Walk-forward analysis: Out-of-sample testing with rolling window optimization                             |        | 0.3.1   |
| Multi-objective optimization: Simultaneous optimization of risk-adjusted returns and drawdown constraints |        | 0.3.2   |

### Production Trading

| Objective                                                                              | Status | Version |
| -------------------------------------------------------------------------------------- | ------ | ------- |
| Live trading mode: Deploy backtested strategies to production with Binance gateway     |        | 0.4.0   |
| Order management system: Position sizing, risk limits, and order execution monitoring  |        | 0.4.1   |
| Real-time performance tracking: Live P&L, position tracking, and performance dashboard |        | 0.4.2   |

### Risk Management & Stress Testing

| Objective                                                                                                          | Status | Version |
| ------------------------------------------------------------------------------------------------------------------ | ------ | ------- |
| Monte Carlo simulation: Statistical robustness testing with multiple simulated scenarios                           |        | 0.5.0   |
| Regime detection: Market condition identification (trending, ranging, high/low volatility regimes)                 |        | 0.5.1   |
| Stress testing framework: Strategy resilience under volatility shocks, regime changes, and market stress scenarios |        | 0.5.2   |
| Portfolio-level risk metrics: Correlation analysis, portfolio VaR, and diversification metrics                     |        | 0.5.3   |

### Multi-Asset & Multi-Strategy Portfolio

| Objective                                                                                           | Status | Version |
| --------------------------------------------------------------------------------------------------- | ------ | ------- |
| Multi-asset support: Extend gateway integration to MetaTrader 5 (MetaAPI) for forex and CFD trading |        | 0.6.0   |
| Portfolio construction: Multi-strategy portfolio allocation with risk parity and optimization       |        | 0.6.1   |
| Cross-asset correlation analysis: Portfolio-level risk management across crypto and forex markets   |        | 0.6.2   |
| Dynamic position sizing: Kelly criterion, fixed fractional, and volatility-based position sizing    |        | 0.6.3   |

---

**Note:**
What we are looking for is a framework where you build a full portfolio (not just one strategy, multi assets multi strategy) easily, backtest, optimize and go to production quickly.
A framework that is open to the complete quantitative finance workflow.
