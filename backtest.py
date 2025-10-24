from pathlib import Path


class Backtest:
    def __init__(self, data_source: Path) -> None:
        self._data_source = data_source

    def run(self) -> None:
        self._load_data()

    def _load_data(self) -> None:
        pass


if __name__ == "__main__":
    backtest = Backtest(data_source=Path("storage/binance/candlesticks/BTCUSDT/1m"))
    backtest.run()
