import datetime

from configs.assets import ASSETS
from configs.timezone import TIMEZONE
from interfaces.asset import AssetInterface
from services.backtest import BacktestService


class Backtest(BacktestService):
    def __init__(
        self,
        asset: AssetInterface,
        from_date: datetime.datetime,
        to_date: datetime.datetime,
        restore_data: bool = False,
    ) -> None:
        super().__init__(asset, from_date, to_date, restore_data)

    def run(self) -> None:
        super().run()


if __name__ == "__main__":
    to_date = datetime.datetime.now(tz=TIMEZONE)
    from_date = to_date - datetime.timedelta(days=365)

    backtest = Backtest(
        asset=ASSETS["btcusdt"],
        from_date=from_date,
        to_date=to_date,
        # restore_data=True,
    )

    backtest.run()
